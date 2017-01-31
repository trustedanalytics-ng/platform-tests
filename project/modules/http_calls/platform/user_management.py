#
# Copyright (c) 2016-2017 Intel Corporation
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

from config import console_url
from ...exceptions import YouMustBeJokingException
from ...http_calls import cloud_foundry as cf
from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider
from ...http_client.http_client_factory import HttpClientFactory


def api_get_organizations(*, client=None):
    """GET /orgs"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="orgs",
        msg="PLATFORM: get org list"
    )


def api_create_organization(*, name, client=None):
    """POST /orgs"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    response = client.request(
        method=HttpMethod.POST,
        path="orgs",
        body={"name": name},
        msg="PLATFORM: create an org"
    )
    return response.strip('"')  # guid is returned together with quotation marks


def api_delete_organization(*, org_guid, client=None):
    """DELETE /orgs/{organization_guid}"""
    ref_org_guid, _ = cf.cf_get_ref_org_and_space_guids()
    if org_guid == ref_org_guid:
        raise YouMustBeJokingException("You're trying to delete the reference org")
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="orgs/{org_guid}",
        path_params={'org_guid': org_guid},
        msg="PLATFORM: delete org"
    )


def api_rename_organization(*, org_guid, new_name, client=None):
    """PUT /orgs/{organization_guid}/name"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.PUT,
        path="orgs/{org_guid}/name",
        path_params={'org_guid': org_guid},
        body={"name": new_name},
        msg="PLATFORM: rename org"
    )


def api_add_organization_user(*, org_guid, username, role=None, client=None):
    """POST /orgs/{organization_guid}/users"""
    body = {
        "username": username,
        "org_guid": org_guid,
        "role": role
    }
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="orgs/{org_guid}/users",
        path_params={'org_guid': org_guid},
        body=body,
        msg="PLATFORM: add user to org"
    )


def api_get_organization_users(*, org_guid, client=None):
    """GET /orgs/{organization_guid}/users"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="orgs/{org_guid}/users",
        path_params={'org_guid': org_guid},
        msg="PLATFORM: get list of users in org"
    )


def api_delete_organization_user(*, org_guid, user_guid, client=None):
    """DELETE /orgs/{organization_guid}/users/{user_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="orgs/{org_guid}/users/{user_guid}",
        path_params={"org_guid": org_guid, "user_guid": user_guid},
        msg="PLATFORM: delete user from org"
    )


def api_update_org_user_role(*, org_guid, user_guid, new_role=None, client=None):
    """POST /orgs/{organization_guid}/users/{user_guid}"""
    body = {}
    if new_role is not None:
        body["role"] = new_role
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="orgs/{org_guid}/users/{user_guid}",
        path_params={'org_guid': org_guid, 'user_guid': user_guid},
        body=body,
        msg="PLATFORM: update user roles in org"
    )


def api_get_invitations(*, client=None):
    """GET /invitations"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="invitations",
        msg="PLATFORM: get list of all invitations"
    )


def api_invite_user(*, email, client=None):
    """POST /invitations"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="invitations",
        body={"email": email},
        msg="PLATFORM: invite new platform user"
    )


def api_delete_invitation(*, email, client=None):
    """DELETE /invitations/{invitation}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="invitations/{invitation}",
        path_params={'invitation': email},
        msg="PLATFORM: delete invitation"
    )


def api_resend_invitation(*, email, client=None):
    """POST /invitations/{invitation}/resend"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="invitations/{invitation}/resend",
        path_params={'invitation': email},
        msg="PLATFORM: resend invitation"
    )


def api_register_new_user(*, code, password=None, org_name=None, client=None):
    """POST /registrations"""
    msg = "PLATFORM: register as a new user"
    body = {}
    if org_name is not None:
        msg += " with new organization"
        body["org"] = org_name
    if password is not None:
        body["password"] = password
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="registrations",
        params={"code": code},
        body=body,
        msg=msg
    )
