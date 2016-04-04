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

from modules.constants import TapComponent as TAP
from modules.http_calls import cloud_foundry as cf
from modules.markers import priority, components
from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import Application, Organization, Space
from tests.fixtures.test_data import TestData


logged_components = (TAP.service_catalog, TAP.user_management)


@pytest.mark.usefixtures("test_org", "test_space", "login_to_cf", "example_app_path")
class TapApp(TapTestCase):

    pytestmark = [components.service_catalog]

    @priority.high
    def test_api_push_stop_start_restage_delete(self):
        self.step("Push example application")
        test_app = Application.push(
            space_guid=TestData.test_space.guid,
            source_directory=TestData.example_app_repo_path
        )
        self.step("Check the application is running")
        self.assertEqualWithinTimeout(120, True, test_app.cf_api_app_is_running)

        self.step("Stop the application and check that it is stopped")
        test_app.api_stop()
        self.assertEqualWithinTimeout(120, False, test_app.cf_api_app_is_running)

        self.step("Start the application and check that it has started")
        test_app.api_start()
        self.assertEqualWithinTimeout(120, True, test_app.cf_api_app_is_running)

        self.step("Delete the application and check that it doesn't exist")
        test_app.api_delete()
        self.assertNotIn(test_app, Application.cf_api_get_list_by_space(TestData.test_space.guid))


class DeleteSpaceAndOrg(TapTestCase):
    pytestmark = [components.user_management, components.service_catalog]

    @pytest.fixture(scope="function", autouse=True)
    def create_org_space_push_app(self, request, example_app_path):
        self.step("Create test organization and space")
        self.test_org = Organization.api_create()
        self.test_space = Space.api_create(self.test_org)
        self.step("Login to cf targeting test org and test space")
        cf.cf_login(self.test_org.name, self.test_space.name)
        self.test_app = Application.push(
            space_guid=self.test_space.guid,
            source_directory=example_app_path
        )
        self.step("Check the application is running")
        self.assertEqualWithinTimeout(120, True, self.test_app.cf_api_app_is_running)

    @priority.low
    def test_delete_space_and_org_after_app_creation_and_deletion(self):
        self.step("Delete the test application")
        self.test_app.api_delete()
        self.step("Delete the space using platform api")
        self.test_space.api_delete()
        self.step("Check that the space is gone")
        self.assertNotInWithRetry(self.test_space, Space.api_get_list)
        self.step("Delete the organization using platform api")
        self.test_org.api_delete()
        self.step("Check that the organization is gone")
        self.assertNotInWithRetry(self.test_org, Organization.api_get_list)

    @priority.low
    def test_delete_space_and_org_without_deleting_an_app(self):
        self.step("Delete the space using platform api")
        self.test_space.api_delete()
        self.step("Check that the space is gone")
        self.assertNotInWithRetry(self.test_space, Space.api_get_list)
        self.step("Delete the test organization using platform api")
        self.test_org.api_delete()
        self.step("Check that the organization is gone")
        self.assertNotInWithRetry(self.test_org, Organization.api_get_list)
