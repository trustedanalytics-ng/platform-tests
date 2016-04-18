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

from .. import Invitation, Organization, User
from ... import gmail_api
from ...api_client import PlatformApiClient
from ...http_calls import platform as api
from ...test_names import get_test_name


def onboard(username=None, password=None, org_name=None, inviting_client=None, check_email=True):
    """
    Onboard new user. Check email for registration code and register.
    Returns objects for newly created user and org.
    """
    password = User.generate_password() if password is None else password
    invitation = Invitation.api_send(username, inviting_client=inviting_client)
    if check_email:
        code = gmail_api.get_invitation_code_for_user(username=invitation.username)
    else:
        code = invitation.code
    return register(code, invitation.username, password, org_name)


def register(code, username, password=None, org_name=None):
    """
    Set password for new user and select name for their organization.
    Returns objects for newly created user and org.
    """
    password = User.generate_password() if password is None else password
    org_name = get_test_name() if org_name is None else org_name
    Organization.TEST_ORG_NAMES.append(org_name)
    User.TEST_USERNAMES.append(username)
    client = PlatformApiClient.get_client(username)
    response = api.api_register_new_user(code, password, org_name, client=client)
    new_org = Organization(name=response["org"], guid=response["orgGuid"])
    new_user = User(guid=response["userGuid"], username=username, password=response["password"],
                    org_roles={new_org.guid: ["managers"]})  # user is an org manager in the organization they create
    return new_user, new_org
