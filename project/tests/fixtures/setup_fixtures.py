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

from configuration import config
from modules import gmail_api
from modules.api_client import PlatformApiClient
from modules.http_calls import platform as api
from modules.tap_object_model import Invitation, Organization, Space, User
from modules.test_names import get_test_name


def create_test_users(number, password=None):
    password = User.generate_password() if password is None else password
    roles = User.ORG_ROLES["manager"]
    org = Organization.api_create()
    usernames = [get_test_name(email=True) for _ in range(number)]
    for username in usernames:
        User.TEST_USERNAMES.append(username)
        api.api_add_organization_user(org.guid, username, roles)
    codes = gmail_api.get_invitation_codes_for_list(usernames)
    for username in usernames:
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(codes[username], password, client=client)
    org_users = User.api_get_list_via_organization(org_guid=org.guid)
    new_users = [user for user in org_users if user.username in usernames]
    if len(new_users) < len(usernames):
        raise AssertionError("Not all users were created")
    for user in new_users:
        user.password = password
    return new_users, org


def get_reference_organization():
    ref_org_name = config.CONFIG["ref_org_name"]
    orgs = Organization.cf_api_get_list()
    return next(o for o in orgs if o.name == ref_org_name)


def get_reference_space():
    ref_space_name = config.CONFIG["ref_space_name"]
    spaces = Space.cf_api_get_list()
    return next(s for s in spaces if s.name == ref_space_name)



