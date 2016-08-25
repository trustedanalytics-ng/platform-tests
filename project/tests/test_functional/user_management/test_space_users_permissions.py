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

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, User, Space
from tests.fixtures.assertions import assert_raises_http_exception, assert_not_in_with_retry, assert_no_errors
from tests.fixtures.test_data import TestData
from config import tap_type
from config import TapType


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]
tap_ng = TapType.tap_ng.value

@pytest.mark.skipif(tap_type == tap_ng, reason="Spaces are not predicted for TAP_NG")
class TestSpaceUserPermissions(object):

    CLIENT_PERMISSION = [
        ("admin", True),
        ("org_manager", True),
        ("space_manager_in_org", True),
        ("org_user", False),
        ("other_org_manager", False),
        ("other_user", False),
    ]

    SPACE_PERMISSION = {
        "admin": True,
        "org_manager": True,
        "space_manager_in_org": False,
        "org_user": False,
        "other_org_manager": False,
        "other_user": False,
    }

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def user_clients(cls, request, test_org, test_space, class_context):
        cls.context = class_context  # TODO move to methods when dependency on unittest is removed
        second_test_org = Organization.api_create(class_context)
        org_manager = User.api_create_by_adding_to_organization(class_context, test_org.guid)
        space_manager_in_org = User.api_create_by_adding_to_space(class_context, test_org.guid, test_space.guid)
        org_user = User.api_create_by_adding_to_organization(class_context, test_org.guid,
                                                             roles=User.ORG_ROLES["auditor"])
        other_org_manager = User.api_create_by_adding_to_organization(class_context, second_test_org.guid)
        other_user = User.api_create_by_adding_to_organization(class_context, second_test_org.guid, roles=[])
        cls.user_clients = {
            "admin": HttpClientFactory.get(ConsoleConfigurationProvider.get()),
            "org_manager": org_manager.login(),
            "space_manager_in_org": space_manager_in_org.login(),
            "org_user": org_user.login(),
            "other_org_manager": other_org_manager.login(),
            "other_user": other_user.login()
        }

    @staticmethod
    def _assert_user_in_space_with_roles(expected_user, space_guid):
        step("Check that the user is on the list of space users")
        space_users = User.api_get_list_via_space(space_guid)
        assert expected_user in space_users
        space_user = next(user for user in space_users if user.guid == expected_user.guid)
        step("Check that the user has expected space roles")
        space_user_roles = space_user.space_roles.get(space_guid)
        expected_roles = expected_user.space_roles.get(space_guid)
        assert space_user_roles == expected_roles, "{} space roles are not equal".format(expected_user)

    @priority.medium
    @pytest.mark.parametrize("client, is_authorized", CLIENT_PERMISSION)
    def test_get_user_list(self, client, is_authorized):
        test_user = User.api_create_by_adding_to_space(self.context, TestData.test_org.guid, TestData.test_space.guid)
        step("Try to get user list from space by using every client type.")
        if is_authorized:
            user_list = User.api_get_list_via_space(TestData.test_space.guid, client=self.user_clients[client])
            assert test_user in user_list, "User {} was not found in list".format(test_user)
        else:
            assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                         User.api_get_list_via_space, TestData.test_space.guid,
                                         client=self.user_clients[client])

    @priority.medium
    @pytest.mark.parametrize("client, is_authorized", CLIENT_PERMISSION)
    def test_add_new_user(self, client, is_authorized):
        step("Try to add new user with each client type.")
        user_list = User.api_get_list_via_space(TestData.test_space.guid)
        if is_authorized:
            test_user = User.api_create_by_adding_to_space(self.context, TestData.test_org.guid,
                                                           TestData.test_space.guid,
                                                           inviting_client=self.user_clients[client])
            self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
        else:
            assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                         User.api_create_by_adding_to_space, self.context,
                                         TestData.test_org.guid, TestData.test_space.guid,
                                         inviting_client=self.user_clients[client])
            assert User.api_get_list_via_space(TestData.test_space.guid) == user_list, "User was added"

    @priority.medium
    @pytest.mark.parametrize("client, is_authorized", CLIENT_PERMISSION)
    def test_add_existing_user(self, client, is_authorized):
        step("Try to add existing user to space with every client type.")
        test_user = User.api_create_by_adding_to_organization(self.context, TestData.test_org.guid)
        if is_authorized:
            test_user.api_add_to_space(TestData.test_space.guid, TestData.test_org.guid,
                                       client=self.user_clients[client])
            self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
        else:
            assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                         User.api_create_by_adding_to_space, self.context,
                                         TestData.test_org.guid, TestData.test_space.guid,
                                         inviting_client=self.user_clients[client])

    @priority.medium
    @pytest.mark.parametrize("client, is_authorized", CLIENT_PERMISSION)
    def test_update_role(self, client, is_authorized):
        new_roles = User.SPACE_ROLES["auditor"]
        step("Try to change user space role using every client type.")
        test_user = User.api_create_by_adding_to_organization(self.context, TestData.test_org.guid)
        if is_authorized:
            test_user.api_update_space_roles(TestData.test_space.guid, new_roles=new_roles,
                                             client=self.user_clients[client])
            self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
        else:
            assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                         test_user.api_update_space_roles, TestData.test_space.guid,
                                         new_roles=new_roles, client=self.user_clients[client])

    @priority.medium
    @pytest.mark.parametrize("client, is_authorized", CLIENT_PERMISSION)
    def test_delete_user(self, client, is_authorized):
        test_user = User.api_create_by_adding_to_organization(self.context, TestData.test_org.guid)
        step("Try to delete user from space using every client type")
        test_user.api_add_to_space(org_guid=TestData.test_org.guid, space_guid=TestData.test_space.guid)
        self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
        if is_authorized:
            test_user.api_delete_from_space(TestData.test_space.guid, client=self.user_clients[client])
            assert_not_in_with_retry(test_user, User.api_get_list_via_space, TestData.test_space.guid)
        else:
            assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                         test_user.api_delete_from_space, TestData.test_space.guid,
                                         client=self.user_clients[client])
            assert test_user in User.api_get_list_via_space(TestData.test_space.guid), "User was deleted"

    @priority.medium
    def test_add_space(self):
        step("Try to add new space using every client type.")
        errors = []
        for client in self.user_clients:
            try:
                space_list = Space.api_get_list_in_org(org_guid=TestData.test_org.guid)
                if self.SPACE_PERMISSION[client]:
                    new_space = Space.api_create(TestData.test_org, client=self.user_clients[client])
                    space_list = Space.api_get_list()
                    assert new_space in space_list, "Space was not created."
                else:
                    assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                 Space.api_create, TestData.test_org,
                                                 client=self.user_clients[client])
                    assert Space.api_get_list_in_org(org_guid=TestData.test_org.guid) == space_list, "Space was created"
            except Exception as e:
                errors.append(e)
        assert_no_errors(errors)

    @priority.medium
    def test_delete_space(self):
        step("Try to delete space using every client type.")
        errors = []
        for client in self.user_clients:
            try:
                new_space = Space.api_create(TestData.test_org)
                if self.SPACE_PERMISSION[client]:
                    new_space.api_delete(client=self.user_clients[client])
                    assert_not_in_with_retry(new_space, Space.api_get_list)
                else:
                    assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                 new_space.api_delete, client=self.user_clients[client])
                    space_list = Space.api_get_list_in_org(org_guid=TestData.test_org.guid)
                    assert new_space in space_list, "Space was not deleted"
            except Exception as e:
                errors.append(e)
        assert_no_errors(errors)
