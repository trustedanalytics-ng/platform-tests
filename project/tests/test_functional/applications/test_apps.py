#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from modules.app_sources import AppSources
from modules.constants import ApplicationPath, HttpStatus, ServiceLabels, ServicePlan, TapComponent as TAP
from modules.exceptions import CommandExecutionException
from modules.http_calls import cloud_foundry as cf
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, User, ServiceType
from modules.tap_object_model.flows import summaries
from tests.fixtures import assertions


logged_components = (TAP.service_catalog, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


@pytest.mark.skip(reason="DPNG-8776 Adjust test_apps tests to TAP NG")
class TestTapApp:

    @pytest.fixture(scope="function")
    def instance(self, context, request, test_org, test_space):
        instance = ServiceInstance.api_create_with_plan_name(context=context, org_guid=test_org.guid,
                                                             space_guid=test_space.guid,
                                                             service_label=ServiceLabels.KAFKA,
                                                             service_plan_name=ServicePlan.SHARED)
        return instance

    @pytest.fixture(scope="function")
    def remove_from_space(self, request, test_space, test_org_manager):
        def fin():
            test_org_manager.api_delete_from_space(space_guid=test_space.guid)
        request.addfinalizer(fin)

    @pytest.fixture(scope="function")
    @pytest.mark.usefixtures("login_to_cf")
    def test_app(self, context, test_space, instance):
        test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
        step("Compile the sources")
        test_app_sources.compile_mvn()
        step("Push application to cf")
        application = Application.push(context, source_directory=ApplicationPath.SAMPLE_JAVA_APP,
                                       space_guid=test_space.guid,
                                       bound_services=(instance.name,))
        step("Check the application is running")
        application.ensure_started()
        return application

    def _check_user_can_do_app_flow(self, test_space, client, context):
        step("Push example application")
        example_app_path = ApplicationPath.SAMPLE_PYTHON_APP
        test_app = Application.push(context, space_guid=test_space.guid, source_directory=example_app_path)
        step("Check the application is running")
        assertions.assert_equal_with_retry(True, test_app.cf_api_app_is_running)
        step("Stop the application and check that it is stopped")
        test_app.stop(client=client)
        assertions.assert_equal_with_retry(False, test_app.cf_api_app_is_running)
        step("Start the application and check that it has started")
        test_app.start(client=client)
        assertions.assert_equal_with_retry(True, test_app.cf_api_app_is_running)
        step("Delete the application and check that it doesn't exist")
        test_app.api_delete(client=client)
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert test_app not in apps

    @priority.high
    def test_admin_can_manage_app(self, test_org, test_space, admin_client, context):
        cf.cf_login(test_org.name, test_space.name)
        self._check_user_can_do_app_flow(test_space, client=admin_client, context=context)

    @priority.high
    @pytest.mark.usefixtures("remove_from_space")
    def test_developer_can_manage_app(self, test_org, test_space, test_org_manager, test_org_manager_client, context):
        space_developer = test_org_manager
        space_developer.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                         roles=User.SPACE_ROLES["developer"])
        cf.cf_login(test_org.name, test_space.name, credentials=(space_developer.username, space_developer.password))
        space_developer_client = test_org_manager_client
        self._check_user_can_do_app_flow(test_space, client=space_developer_client, context=context)

    @priority.low
    @pytest.mark.usefixtures("remove_from_space")
    def test_non_developer_cannot_push_app(self, context, test_org, test_space, test_org_manager):
        step("Add user to space as manager")
        space_manager = test_org_manager
        space_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                       roles=User.SPACE_ROLES["manager"])
        step("Login as this user")
        cf.cf_login(test_org.name, test_space.name, credentials=(space_manager.username, space_manager.password))

        step("Check that manager cannot push app")
        example_app_path = ApplicationPath.SAMPLE_PYTHON_APP
        with pytest.raises(CommandExecutionException):
            Application.push(context, space_guid=test_space.guid, source_directory=example_app_path)

    @priority.low
    def test_non_developer_cannot_manage_app(self, context, test_org, test_space, test_org_manager,
                                             test_org_manager_client):
        step("Push example app as admin")
        cf.cf_login(test_org.name, test_space.name)
        example_app_path = ApplicationPath.SAMPLE_PYTHON_APP
        test_app = Application.push(context, space_guid=test_space.guid, source_directory=example_app_path)
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert test_app in apps

        step("Add user to space as manager")
        space_manager = test_org_manager
        space_manager_client = test_org_manager_client
        space_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                       roles=User.SPACE_ROLES["manager"])
        step("Check that manager cannot stop app")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                test_app.stop, client=space_manager_client)
        step("Check that manager cannot start app")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                test_app.start, client=space_manager_client)
        step("Check that manager cannot delete app")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                test_app.api_delete, client=space_manager_client)
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

    @priority.medium
    def test_cascade_app_delete(self, test_space, instance, test_app):
        test_app.api_delete(cascade=True)
        cf_apps_list, cf_service_instances_list = summaries.cf_api_get_space_summary(test_space.guid)
        assert instance not in cf_service_instances_list and test_app not in cf_apps_list

    @priority.medium
    @pytest.mark.sample_apps_test
    def test_app_register_in_marketplace(self, context, test_org, test_space, sample_java_app):
        register_service = ServiceType.register_app_in_marketplace(context, sample_java_app.name, sample_java_app.guid,
                                                                   test_org.guid, test_space.guid)
        services = ServiceType.cf_api_get_list_from_marketplace_by_space(test_space.guid)
        assert register_service in services

    @priority.medium
    @pytest.mark.sample_apps_test
    def test_delete_app(self, test_space, sample_java_app):
        sample_java_app.api_delete()
        cf_apps_list, _ = summaries.cf_api_get_space_summary(test_space.guid)
        assert sample_java_app not in cf_apps_list
