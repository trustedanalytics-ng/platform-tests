#
# Copyright (c) 2015-2016 Intel Corporation
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

from modules.constants import TapComponent as TAP
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, User
from tests.fixtures import assertions


logged_components = (TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
pytestmark = [components.auth_gateway, components.auth_proxy, components.user_management]


class TestOrganization:

    @priority.high
    def test_create_delete_organization(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Check that the organization is on the organization list")
        orgs = Organization.api_get_list()
        assert test_org in orgs
        step("Delete the organization")
        test_org.api_delete()
        step("Check that the organization is not on org list")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)

    @priority.medium
    def test_rename_organization(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Update the organization, giving it new name")
        new_name = "new-{}".format(test_org.name)
        test_org.rename(new_name)
        step("Check that the organization with new name is on the organization list")
        orgs = Organization.api_get_list()
        assert test_org in orgs

    @priority.low
    def test_delete_organization_with_user(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Add new platform user to the organization")
        User.api_create_by_adding_to_organization(context, test_org.guid)
        step("Delete the organization")
        test_org.api_delete()
        step("Check that the organization is not on org list")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)
