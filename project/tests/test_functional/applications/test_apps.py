#
# Copyright (c) 2015 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from modules.constants import TapComponent as TAP, HttpStatus
from modules.exceptions import CommandExecutionException
from modules.http_calls import cloud_foundry as cf
from modules.markers import priority, components
from modules.tap_logger import step
from modules.tap_object_model import Application, User
from tests.fixtures import assertions


logged_components = (TAP.service_catalog, TAP.user_management)
pytestmark = [components.service_catalog]


class TestTapApp:

    @pytest.fixture(scope="function")
    def remove_from_space(self, request, test_space, test_org_manager):
        def fin():
            test_org_manager.api_delete_from_space(space_guid=test_space.guid)
        request.addfinalizer(fin)

    def _check_user_can_do_app_flow(self, test_org, test_space, example_app_path, client):
        step("Push example application")
        test_app = Application.push(space_guid=test_space.guid, source_directory=example_app_path)
        step("Check the application is running")
        assertions.assert_equal_with_retry(True, test_app.cf_api_app_is_running)
        step("Stop the application and check that it is stopped")
        test_app.api_stop(client=client)
        assertions.assert_equal_with_retry(False, test_app.cf_api_app_is_running)
        step("Start the application and check that it has started")
        test_app.api_start(client=client)
        assertions.assert_equal_with_retry(True, test_app.cf_api_app_is_running)
        step("Delete the application and check that it doesn't exist")
        test_app.api_delete(client=client)
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert test_app not in apps

    @priority.high
    def test_admin_can_manage_app(self, test_org, test_space, example_app_path, admin_client):
        cf.cf_login(test_org.name, test_space.name)
        self._check_user_can_do_app_flow(test_org, test_space, example_app_path, client=admin_client)

    @priority.high
    def test_developer_can_manage_app(self, test_org, test_space, example_app_path, test_org_manager,
                                      remove_from_space):
        space_developer = test_org_manager
        space_developer.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                         roles=User.SPACE_ROLES["developer"])

        cf.cf_login(test_org.name, test_space.name, credentials=(space_developer.username, space_developer.password))
        self._check_user_can_do_app_flow(test_org, test_space, example_app_path, client=space_developer.get_client())

    @priority.low
    def test_non_developer_cannot_push_app(self, test_org, test_space, example_app_path, test_org_manager,
                                           remove_from_space):
        step("Add user to space as manager")
        space_manager = test_org_manager
        space_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                       roles=User.SPACE_ROLES["manager"])
        step("Login as this user")
        cf.cf_login(test_org.name, test_space.name, credentials=(space_manager.username, space_manager.password))

        step("Check that manager cannot push app")
        with pytest.raises(CommandExecutionException):
            Application.push(space_guid=test_space.guid, source_directory=example_app_path)

    @priority.low
    def test_non_developer_cannot_manage_app(self, test_org, test_space, example_app_path, test_org_manager,
                                             remove_from_space):
        step("Push example app as admin")
        cf.cf_login(test_org.name, test_space.name)
        test_app = Application.push(space_guid=test_space.guid, source_directory=example_app_path)
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert test_app in apps

        step("Add user to space as manager")
        space_manager = test_org_manager
        space_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                       roles=User.SPACE_ROLES["manager"])
        step("Check that manager cannot stop app")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                test_app.api_stop, client=space_manager.get_client())
        step("Check that manager cannot start app")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                test_app.api_start, client=space_manager.get_client())
        step("Check that manager cannot delete app")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                test_app.api_delete, client=space_manager.get_client())
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert test_app in apps

    @priority.medium
    def test_compare_app_list_with_cf(self, core_space):
        step("Get application list from platform")
        platform_app_list = Application.api_get_list(core_space.guid)
        step("Get application list from cf")
        cf_app_list = Application.cf_api_get_list_by_space(core_space.guid)
        step("Compare app lists from platform and cf")
        assert sorted(platform_app_list) == sorted(cf_app_list)
