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

from .. import gmail_api
from ..api_client import PlatformApiClient
from configuration import config
from ..exceptions import UnexpectedResponseError, NoSuchUserException
from ..http_calls import cloud_foundry as cf, platform as api, uaa
from ..tap_logger import get_logger
from ..test_names import get_test_name
from . import Organization


logger = get_logger(__name__)


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
    TEST_USERS = []
    TEST_INVITED_EMAILS = []

    def __init__(self, guid=None, username=None, password=None, org_roles=None, space_roles=None):
        self.guid, self.username, self.password = guid, username, password
        self.org_roles = org_roles or {}
        self.space_roles = space_roles or {}

    def __repr__(self):
        return "{0} (username={1}, guid={2})".format(self.__class__.__name__, self.username, self.guid)

    def __eq__(self, other):
        return self.username == other.username and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    def __hash__(self):
        return hash((self.guid, self.username))

    @classmethod
    def api_onboard(cls, username=None, password="testPassw0rd", org_name=None, inviting_client=None):
        """Onboarding of a new user. Return new User and Organization objects."""
        username = cls.api_invite(username, inviting_client)
        code = gmail_api.get_invitation_code_for_user(username)
        return cls.api_register_after_onboarding(code, username, password, org_name)

    @classmethod
    def api_onboard_without_email(cls, username=None, password="testPassw0rd", org_name=None, inviting_client=None):
        """Onboarding of a new user without email. Return new User and Organization objects."""
        username = get_test_name(email=True) if username is None else username
        response = api.api_invite_user(username, client=inviting_client)
        code = gmail_api.extract_code_from_message(response["details"])
        return cls.api_register_after_onboarding(code, username, password, org_name)

    @classmethod
    def api_invite(cls, username=None, inviting_client=None):
        """Send invitation to a new user using inviting_client."""
        username = get_test_name(email=True) if username is None else username
        api.api_invite_user(username, client=inviting_client)
        cls.TEST_INVITED_EMAILS.append(username)
        return username

    @classmethod
    def api_register_after_onboarding(cls, code, username, password="testPassw0rd", org_name=None):
        """Set password for new user and select name for their organization. Return objects for new user and org"""
        org_name = get_test_name() if org_name is None else org_name
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, org_name, client=client)
        # need to obtain org guid (DPNG-2149)
        new_org = next(o for o in Organization.api_get_list() if o.name == org_name)
        Organization.TEST_ORGS.append(new_org)
        # need to obtain user's guid (DPNG-2149)
        org_users = cls.api_get_list_via_organization(org_guid=new_org.guid)
        new_user = next(u for u in org_users if u.username == username)
        new_user.password = password
        new_user.org_roles[new_org.guid] = ["managers"]  # user is an org manager in the organization they create
        cls.TEST_USERS.append(new_user)
        return new_user, new_org

    @classmethod
    def api_create_by_adding_to_organization(cls, org_guid, username=None, password="testPassw0rd",
                                             roles=ORG_ROLES["manager"], inviting_client=None):
        username = get_test_name(email=True) if username is None else username
        cls.TEST_INVITED_EMAILS.append(username)
        api.api_add_organization_user(org_guid, username, roles, client=inviting_client)
        code = gmail_api.get_invitation_code_for_user(username)
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, client=client)
        org_users = cls.api_get_list_via_organization(org_guid=org_guid)
        new_user = next((user for user in org_users if user.username == username), None)
        if new_user is None:
            raise AssertionError("New user was not found in the organization")
        new_user.password = password
        cls.TEST_USERS.append(new_user)
        return new_user

    @classmethod
    def api_create_users_for_tests(cls, number, password="testPassw0rd"):
        roles = cls.ORG_ROLES["manager"]
        org = Organization.api_create()
        usernames = [get_test_name(email=True) for _ in range(number)]
        for username in usernames:
            cls.TEST_INVITED_EMAILS.append(username)
            api.api_add_organization_user(org.guid, username, roles)
        codes = gmail_api.get_invitation_codes_for_list(usernames)
        for username in usernames:
            client = PlatformApiClient.get_client(username)
            api.api_register_new_user(codes[username], password, client=client)
        org_users = cls.api_get_list_via_organization(org_guid=org.guid)
        new_users = [user for user in org_users if user.username in usernames]
        if len(new_users) < len(usernames):
            raise AssertionError("Not all users were created")
        for user in new_users:
            user.password = password
            cls.TEST_USERS.append(user)
        return new_users, org

    @classmethod
    def api_create_by_adding_to_space(cls, org_guid, space_guid, username=None, password="testPassw0rd",
                                      roles=SPACE_ROLES["manager"], inviting_client=None):
        username = get_test_name(email=True) if username is None else username
        cls.TEST_INVITED_EMAILS.append(username)
        api.api_add_space_user(org_guid, space_guid, username, roles, inviting_client)
        code = gmail_api.get_invitation_code_for_user(username)
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, client=client)
        space_users = cls.api_get_list_via_space(space_guid)
        new_user = next((user for user in space_users if user.username == username), None)
        new_user.password = password
        cls.TEST_USERS.append(new_user)
        return new_user

    @classmethod
    def api_get_list_via_organization(cls, org_guid, client=None):
        response = api.api_get_organization_users(org_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.org_roles[org_guid] = user_data["roles"]
            users.append(user)
        return users

    @classmethod
    def api_get_list_via_space(cls, space_guid, client=None):
        response = api.api_get_space_users(space_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.space_roles[space_guid] = user_data["roles"]
            users.append(user)
        return users

    @classmethod
    def api_get_pending_invitations(cls, client=None):
        return api.api_get_invitations(client=client)

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
        api.api_add_organization_user(org_guid, self.username, roles, client=client)
        self.org_roles[org_guid] = list(set(self.org_roles.get(org_guid, set())) | set(roles))

    def api_add_to_space(self, space_guid, org_guid, roles=SPACE_ROLES["manager"], client=None):
        api.api_add_space_user(org_guid=org_guid, space_guid=space_guid, username=self.username,
                               roles=roles, client=client)
        self.space_roles[space_guid] = list(roles)

    def api_update_org_roles(self, org_guid, new_roles=None, client=None):
        api.api_update_org_user_roles(org_guid, self.guid, new_roles, client=client)
        self.org_roles[org_guid] = list(new_roles)

    def api_update_space_roles(self, space_guid, new_roles=None, client=None):
        api.api_update_space_user_roles(space_guid, self.guid, new_roles, client=client)
        if new_roles is not None:
            self.space_roles[space_guid] = list(new_roles)

    def api_delete_from_organization(self, org_guid, client=None):
        api.api_delete_organization_user(org_guid, self.guid, client=client)

    def api_delete_from_space(self, space_guid, client=None):
        api.api_delete_space_user(space_guid, self.guid, client=client)

    @staticmethod
    def api_delete_user_invitation(username, client=None):
        api.api_delete_invitation(username, client=client)

    @staticmethod
    def api_resend_user_invitation(username, client=None):
        api.api_resend_invitation(username, client=client)

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

    def cf_api_delete(self):
        cf.cf_api_delete_user(self.guid)
        uaa.uaa_api_user_delete(self.guid)

    @classmethod
    def cf_api_tear_down_test_users(cls):
        """Use this method in tearDown and tearDownClass."""
        while len(cls.TEST_USERS) > 0:
            test_user = cls.TEST_USERS.pop()
            try:
                test_user.cf_api_delete()
            except UnexpectedResponseError as e:
                logger.warning("Failed to delete {}: {}".format(test_user, e.error_message))

    @classmethod
    def api_tear_down_test_invitations(cls):
        """Use this method in tearDown and tearDownClass."""
        pending_invites = cls.api_get_pending_invitations()
        cls.TEST_INVITED_EMAILS = [e for e in cls.TEST_INVITED_EMAILS if e in pending_invites]
        while len(cls.TEST_INVITED_EMAILS) > 0:
            test_invited = cls.TEST_INVITED_EMAILS.pop()
            try:
                cls.api_delete_user_invitation(test_invited)
            except UnexpectedResponseError as e:
                logger.warning("Failed to delete {}: {}".format(test_invited, e.error_message))


