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

from configuration.config import CONFIG
from modules.constants import ApplicationPath, TapComponent as TAP
from modules.http_calls import cloud_foundry as cf
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import Application, Organization, Space
from tests.fixtures import assertions


logged_components = (TAP.user_management, TAP.service_catalog)
pytestmark = [components.user_management, components.service_catalog]



class TestDeleteSpaceAndOrg:

    @pytest.fixture(scope="function")
    def org_space_app(self, context):
        step("Create test organization and space")
        test_org = Organization.api_create(context)
        test_space = Space.api_create(test_org)
        step("Login to cf targeting test org and test space")
        cf.cf_login(test_org.name, test_space.name)
        step("Push example app")
        example_app_path = ApplicationPath.SAMPLE_APP
        test_app = Application.push(space_guid=test_space.guid, source_directory=example_app_path,
                                    env_proxy=CONFIG["pushed_app_proxy"])
        return test_org, test_space, test_app

    def _delete_org_space(self, test_org, test_space):
        step("Delete the space using platform api")
        test_space.api_delete()
        step("Check that the space is gone")
        assertions.assert_not_in_with_retry(test_space, Space.api_get_list)
        step("Delete the organization using platform api")
        test_org.api_delete()
        step("Check that the organization is gone")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)

    @priority.low
    def test_delete_space_and_org_after_app_creation_and_deletion(self, org_space_app):
        test_org, test_space, test_app = org_space_app
        step("Delete test application")
        test_app.api_delete()
        self._delete_org_space(test_org, test_space)

    @priority.low
    def test_delete_space_and_org_without_deleting_an_app(self, org_space_app):
        test_org, test_space, _ = org_space_app
        self._delete_org_space(test_org, test_space)
