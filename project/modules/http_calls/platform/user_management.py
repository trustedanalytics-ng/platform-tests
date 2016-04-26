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

from modules.exceptions import YouMustBeJokingException
from modules.api_client import PlatformApiClient
from modules.http_calls import cloud_foundry as cf


def api_get_organizations(client=None):
    """GET /rest/orgs"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs", log_msg="PLATFORM: get org list")


def api_create_organization(name, client=None):
    """POST /rest/orgs"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/orgs", body={"name": name}, log_msg="PLATFORM: create an org")
    return response.strip('"')  # guid is returned together with quotation marks


def api_delete_organization(org_guid, client=None):
    """DELETE /rest/orgs/{organization_guid}"""
    ref_org_guid, _ = cf.cf_get_ref_org_and_space_guids()
    if org_guid == ref_org_guid:
        raise YouMustBeJokingException("You're trying to delete the reference org")
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/orgs/{}".format(org_guid), log_msg="PLATFORM: delete org")


def api_rename_organization(org_guid, new_name, client=None):
    """PUT /rest/orgs/{organization_guid}/name"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("PUT", "rest/orgs/{}/name".format(org_guid), body={"name": new_name},
                          log_msg="PLATFORM: rename org")


def api_add_organization_user(org_guid, username, roles=(), client=None):
    """POST /rest/orgs/{organization_guid}/users"""
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": list(roles)
    }
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/orgs/{}/users".format(org_guid), body=body, log_msg="PLATFORM: add user to org")


def api_get_organization_users(org_guid, client=None):
    """GET /rest/orgs/{organization_guid}/users"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs/{}/users".format(org_guid), log_msg="PLATFORM: get list of users in org")


def api_delete_organization_user(org_guid, user_guid, client=None):
    """DELETE /rest/orgs/{organization_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/orgs/{}/users/{}".format(org_guid, user_guid),
                          log_msg="PLATFORM: delete user from org")


def api_update_org_user_roles(org_guid, user_guid, new_roles=None, client=None):
    """POST /rest/orgs/{organization_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    body = {}
    if new_roles is not None:
        body["roles"] = list(new_roles)
    return client.request("POST", "rest/orgs/{}/users/{}".format(org_guid, user_guid), body=body,
                          log_msg="PLATFORM: update user roles in org")


def api_add_space_user(org_guid, space_guid, username, roles=(), client=None):
    """POST /rest/spaces/{space_guid}/users"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": list(roles)
    }
    return client.request("POST", "rest/spaces/{}/users".format(space_guid), body=body,
                          log_msg="PLATFORM: Add user to space")


def api_get_space_users(space_guid, client=None):
    """GET /rest/spaces/{space_guid}/users"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/spaces/{}/users".format(space_guid), log_msg="PLATFORM: get space users")


def api_delete_space_user(space_guid, user_guid, client=None):
    """DELETE /rest/spaces/{space_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/spaces/{}/users/{}".format(space_guid, user_guid),
                          log_msg="PLATFORM: delete user from space")


def api_update_space_user_roles(space_guid, user_guid, new_roles=None, client=None):
    """POST /rest/spaces/{space_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    body = {}
    if new_roles is not None:
        body["roles"] = list(new_roles)
    return client.request("POST", "rest/spaces/{}/users/{}".format(space_guid, user_guid), body=body,
                          log_msg="PLATFORM: update user roles in space")


def api_get_invitations(client=None):
    """GET /rest/invitations"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/invitations", log_msg="PLATFORM: get list of all invitations")


def api_invite_user(email, client=None):
    """POST /rest/invitations"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/invitations", body={"email": email},
                          log_msg="PLATFORM: invite new platform user")


def api_delete_invitation(email, client=None):
    """DELETE /rest/invitations/{invitation}"""
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/invitations/{}".format(email), log_msg="PLATFORM: delete invitation")


def api_resend_invitation(email, client=None):
    """POST /rest/invitations/{invitation}/resend"""
    client = client or PlatformApiClient.get_admin_client()
    client.request("POST", "rest/invitations/{}/resend".format(email), log_msg="PLATFORM: resend invitation")


def api_register_new_user(code, password=None, org_name=None, client=None):
    """POST /rest/registrations"""
    msg = "PLATFORM: register as a new user"
    if org_name is not None:
        msg += " with new organization"
    client = client or PlatformApiClient.get_admin_client()
    body = {}
    if org_name is not None:
        body["org"] = org_name
    if password is not None:
        body["password"] = password
    return client.request("POST", "rest/registrations", params={"code": code}, body=body, log_msg=msg)


def api_get_spaces_in_org(org_guid, client=None):
    """GET /rest/orgs/{org}/spaces"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs/{}/spaces".format(org_guid), log_msg="PLATFORM: get list of spaces in org")


def api_get_spaces(client=None):
    """GET /rest/spaces"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/spaces", log_msg="PLATFORM: get list of all spaces")


def api_create_space(org_guid, name, client=None):
    """POST /rest/spaces"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/spaces", body={"name": name, "org_guid": org_guid},
                              log_msg="PLATFORM: create a space")
    if response == "":
        raise AssertionError("Response to POST /rest/spaces did not return space guid.")
    return response


def api_delete_space(space_guid, client=None):
    """DELETE /rest/spaces/{space}"""
    _, ref_space_guid = cf.cf_get_ref_org_and_space_guids()
    if space_guid == ref_space_guid:
        raise YouMustBeJokingException("You're trying to delete the reference space")
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/spaces/{}".format(space_guid), log_msg="PLATFORM: delete space")
