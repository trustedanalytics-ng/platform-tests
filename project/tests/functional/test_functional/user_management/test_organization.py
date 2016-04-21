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
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import Organization, User


@log_components()
@components(TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
class TestOrganization(TapTestCase):

    @classmethod
    def tearDownClass(cls):
        User.cf_api_tear_down_test_users()
        User.api_tear_down_test_invitations()
        Organization.cf_api_tear_down_test_orgs()

    @priority.high
    def test_create_organization(self):
        self.step("Create an organization")
        expected_org = Organization.api_create()
        self.step("Check that the organization is on the organization list")
        orgs = Organization.api_get_list()
        self.assertIn(expected_org, orgs)

    @priority.medium
    def test_rename_organization(self):
        self.step("Create an organization")
        expected_org = Organization.api_create()
        self.step("Update the organization, giving it new name")
        new_name = "new-{}".format(expected_org.name)
        expected_org.rename(new_name)
        self.step("Check that the organization with new name is on the organization list")
        orgs = Organization.api_get_list()
        self.assertIn(expected_org, orgs)

    @priority.high
    def test_delete_organization(self):
        self.step("Create an organization")
        deleted_org = Organization.api_create()
        self.step("Check that the organization is on the org list")
        orgs = Organization.api_get_list()
        self.assertIn(deleted_org, orgs)
        self.step("Delete the organization")
        deleted_org.api_delete()
        self.step("Check that the organization is not on org list")
        self.assertNotInWithRetry(deleted_org, Organization.api_get_list)

    @priority.medium
    def test_get_more_than_50_organizations(self):
        self.step("Get list of organization and check how many there are")
        old_orgs = Organization.api_get_list()
        self.step("Add organizations, so that there are more than 50")
        new_orgs_num = (50 - len(old_orgs)) + 1
        new_orgs = [Organization.api_create() for _ in range(new_orgs_num)]
        self.step("Check that all new and old organizations are returned in org list")
        expected_orgs = old_orgs + new_orgs
        orgs = Organization.api_get_list()
        self.assertGreaterEqual(len(orgs), len(expected_orgs))
        missing_orgs = [o for o in expected_orgs if o not in orgs]
        self.assertEqual(missing_orgs, [], "Not all test orgs are present on org list")

    @priority.low
    def test_delete_organization_with_user(self):
        self.step("Create an organization")
        org = Organization.api_create()
        self.step("Add new platform user to the organization")
        User.api_create_by_adding_to_organization(org.guid)
        self.step("Delete the organization")
        org.api_delete()
        self.step("Check that the organization is not on org list")
        self.assertNotInWithRetry(org, Organization.api_get_list)
