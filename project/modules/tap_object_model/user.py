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

import functools
import random
import string

from configuration import config
from .. import gmail_api
from ..api_client import PlatformApiClient
from ..exceptions import NoSuchUserException
from ..http_calls import cloud_foundry as cf, uaa
from ..http_calls.platform import user_management
from ..test_names import generate_test_object_name


@functools.total_ordering
class User(object):

    __ADMIN = None
    ORG_ROLES = {
        "manager": {"managers"},
        "auditor": {"auditors"},
        "billing_manager": {"billing_managers"}
    }
    SPACE_ROLES = {
        "manager": {"managers"},
        "auditor": {"auditors"},
        "developer": {"developers"}
    }

    def __init__(self, guid=None, username=None, password=None, org_roles=None, space_roles=None):
        self.guid = guid
        self.username = username
        self.password = password
        self.org_roles = org_roles or {}
        self.space_roles = space_roles or {}

    def __repr__(self):
        return "{} (username={}, guid={})".format(self.__class__.__name__, self.username, self.guid)

    def __eq__(self, other):
        return self.username == other.username and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    def __hash__(self):
        return hash((self.guid, self.username))

    @staticmethod
    def generate_password(length=20):
        base = string.ascii_letters + string.digits
        return "".join([random.choice(base) for _ in range(length)])

    @classmethod
    def api_create_by_adding_to_organization(cls, context, org_guid, username=None, password=None,
                                             roles=ORG_ROLES["manager"], inviting_client=None):
        username = generate_test_object_name(email=True) if username is None else username
        password = cls.generate_password() if password is None else password
        user_management.api_add_organization_user(org_guid, username, roles, client=inviting_client)
        code = gmail_api.get_invitation_code_for_user(username)
        client = PlatformApiClient.get_client(username)
        user_management.api_register_new_user(code, password, client=client)
        org_users = cls.api_get_list_via_organization(org_guid=org_guid)
        new_user = next((user for user in org_users if user.username == username), None)
        if new_user is None:
            raise AssertionError("New user was not found in the organization")
        context.users.append(new_user)
        new_user.password = password
        return new_user

    @classmethod
    def api_create_by_adding_to_space(cls, context, org_guid, space_guid, username=None, password=None,
                                      roles=SPACE_ROLES["manager"], inviting_client=None):
        username = generate_test_object_name(email=True) if username is None else username
        password = cls.generate_password() if password is None else password
        user_management.api_add_space_user(org_guid, space_guid, username, roles, inviting_client)
        code = gmail_api.get_invitation_code_for_user(username)
        client = PlatformApiClient.get_client(username)
        user_management.api_register_new_user(code, password, client=client)
        space_users = cls.api_get_list_via_space(space_guid)
        new_user = next((user for user in space_users if user.username == username), None)
        context.users.append(new_user)
        new_user.password = password
        return new_user

    @classmethod
    def api_get_list_via_organization(cls, org_guid, client=None):
        response = user_management.api_get_organization_users(org_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.org_roles[org_guid] = user_data["roles"]
            users.append(user)
        return users

    @classmethod
    def api_get_list_via_space(cls, space_guid, client=None):
        response = user_management.api_get_space_users(space_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.space_roles[space_guid] = user_data["roles"]
            users.append(user)
        return users

    def login(self):
        """Return a logged-in API client for this user."""
        client = PlatformApiClient.get_client(self.username)
        client.authenticate(self.password)
        return client

    def get_client(self):
        """Return API client for this user."""
        client = PlatformApiClient.get_client(self.username)
        return client

    def api_add_to_organization(self, org_guid, roles=ORG_ROLES["manager"], client=None):
        user_management.api_add_organization_user(org_guid, self.username, roles, client=client)
        self.org_roles[org_guid] = list(set(self.org_roles.get(org_guid, set())) | set(roles))

    def api_add_to_space(self, space_guid, org_guid, roles=SPACE_ROLES["manager"], client=None):
        user_management.api_add_space_user(org_guid=org_guid, space_guid=space_guid, username=self.username,
                               roles=roles, client=client)
        self.space_roles[space_guid] = list(roles)

    def api_update_org_roles(self, org_guid, new_roles=None, client=None):
        user_management.api_update_org_user_roles(org_guid, self.guid, new_roles, client=client)
        self.org_roles[org_guid] = list(new_roles)

    def api_update_space_roles(self, space_guid, new_roles=None, client=None):
        user_management.api_update_space_user_roles(space_guid, self.guid, new_roles, client=client)
        if new_roles is not None:
            self.space_roles[space_guid] = list(new_roles)

    def api_delete_from_organization(self, org_guid, client=None):
        user_management.api_delete_organization_user(org_guid, self.guid, client=client)

    def api_delete_from_space(self, space_guid, client=None):
        user_management.api_delete_space_user(space_guid, self.guid, client=client)

    @classmethod
    def get_admin(cls):
        """Return User object for admin user"""
        if cls.__ADMIN is None:
            cls.__ADMIN = cls.cf_api_get_user(config.CONFIG["admin_username"])
            cls.__ADMIN.password = config.CONFIG["admin_password"]
        return cls.__ADMIN

    @classmethod
    def _get_user_list_from_cf_api_response(cls, response):
        users = []
        for user_data in response:
            user = cls(username=user_data["entity"].get("username"), guid=user_data["metadata"].get("guid"))
            users.append(user)
        return users

    @classmethod
    def cf_api_get_all_users(cls):
        response = cf.cf_api_get_users()
        return cls._get_user_list_from_cf_api_response(response)

    @classmethod
    def cf_api_get_user(cls, username):
        users = User.cf_api_get_all_users()
        user = next((user for user in users if user.username == username), None)
        if not user:
            raise NoSuchUserException(username)
        return user

    @classmethod
    def cf_api_get_list_in_organization(cls, org_guid, space_guid=None):
        response = cf.cf_api_get_org_users(org_guid=org_guid, space_guid=space_guid)
        return cls._get_user_list_from_cf_api_response(response)

    def cleanup(self):
        cf.cf_api_delete_user(self.guid)
        # uaa.uaa_api_user_delete(self.guid)
