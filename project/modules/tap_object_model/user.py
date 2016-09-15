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

import functools
import random
import string

import config
from .. import gmail_api
from ..http_calls.platform import user_management as um
from ..http_client.configuration_provider.console_no_auth import ConsoleNoAuthConfigurationProvider
from ..http_client.http_client_factory import HttpClientFactory
from ..http_client.configuration_provider.console import ConsoleConfigurationProvider
from ..test_names import generate_test_object_name
from ..constants import Guid


@functools.total_ordering
class User(object):

    __ADMIN = None

    ORG_ROLE = {
        "admin": "ADMIN",
        "user": "USER",
    }

    def __init__(self, guid=None, username=None, password=None, org_role=None):
        self.guid = guid
        self.username = username
        self.password = password
        self.org_role = org_role or {}
        self.client = None
        self.client_configuration = None

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
    def create_by_adding_to_organization(cls, context, org_guid, username=None, password=None, role=None,
                                         inviting_client=None):
        username = generate_test_object_name(email=True) if username is None else username
        password = cls.generate_password() if password is None else password
        um.api_add_organization_user(org_guid, username, role, client=inviting_client)
        code = gmail_api.get_invitation_code_for_user(username)
        client = HttpClientFactory.get(ConsoleNoAuthConfigurationProvider.get(username))
        um.api_register_new_user(code, password, client=client)
        org_users = cls.get_list_in_organization(org_guid=org_guid)
        new_user = next((user for user in org_users if user.username == username), None)
        if new_user is None:
            raise AssertionError("New user was not found in the organization")
        context.users.append(new_user)
        new_user.password = password
        return new_user

    @classmethod
    def get_list_in_organization(cls, org_guid, client=None):
        response = um.api_get_organization_users(org_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.org_role[org_guid] = user_data["role"]
            users.append(user)
        return users

    def login(self):
        """Return a logged-in API client for this user."""
        self.client_configuration = ConsoleConfigurationProvider.get(self.username, self.password)
        self.client = HttpClientFactory.get(self.client_configuration)
        return self.client

    def get_client(self):
        """Return API client for this user."""
        if self.client is not None:
            return self.client
        return HttpClientFactory.get(ConsoleNoAuthConfigurationProvider.get(self.username))

    def add_to_organization(self, org_guid, role=ORG_ROLE["user"], client=None):
        um.api_add_organization_user(org_guid, self.username, role, client=client)
        self.org_role[org_guid] = list(set(self.org_role.get(org_guid, set())) | set(role))

    def update_org_role(self, org_guid, new_role=None, client=None):
        um.api_update_org_user_role(org_guid, self.guid, new_role, client=client)
        self.org_role[org_guid] = list(new_role)

    def delete_from_organization(self, org_guid, client=None):
        um.api_delete_organization_user(org_guid, self.guid, client=client)

    @classmethod
    def get_admin(cls):
        """Return User object for admin user"""
        users = User.get_all_users()
        admin = next((user for user in users if user.username == config.admin_username), None)
        if admin is None:
            raise AssertionError("Admin with username {} not found".format(config.admin_username))
        return admin

    @classmethod
    def get_all_users(cls):
        # TODO: For now we have only one org. To be changed in Tap v0.9
        return cls.get_list_in_organization(org_guid=Guid.CORE_ORG_GUID)

    def cleanup(self):
        self.delete_from_organization(org_guid=Guid.CORE_ORG_GUID)
