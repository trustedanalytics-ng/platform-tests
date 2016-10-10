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

import config
from .. import command as cmd
from ..constants import LoggerType
from ..exceptions import YouMustBeJokingException
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.configuration_provider.cloud_foundry import CloudFoundryConfigurationProvider
from ..http_client.http_client_factory import HttpClientFactory
from ..tap_logger import get_logger, log_command

# ====================================================== cf cli ====================================================== #

cli_logger = get_logger(LoggerType.CF_CLI)


def cf_login(organization_name, space_name, credentials=None):
    if credentials is None:
        username = config.admin_username
        password = config.admin_password
    else:
        username = credentials[0]
        password = credentials[1]
    command = ["cf", "login", "-a", config.cf_api_url, "-u", username, "-p", password, "-o", organization_name, "-s", space_name]
    if not config.ssl_validation:
        command.append("--skip-ssl-validation")
    log_command(command)
    cmd.run(command)


def cf_push(local_path, local_jar, name=None):
    command = ["cf", "push", "-f", local_path, "-p", local_jar]
    if name:
        command.extend(["-n", name])
    log_command(command)
    return cmd.run(command)


def cf_create_service(broker_name, plan, instance_name):
    command = ["cf", "create-service", broker_name, plan, instance_name]
    log_command(command)
    return cmd.run(command)


def cf_delete(app_name):
    command = ["cf", "delete", app_name, "-f"]
    log_command(command)
    cmd.run(command)


def cf_env(app_name):
    command = ["cf", "env", app_name]
    log_command(command)
    return cmd.run(command)


def cf_delete_service(service):
    command = ["cf", "delete-service", service, "-f"]
    log_command(command)
    return cmd.run(command)


# ====================================================== cf api ====================================================== #

def __get_all_pages(endpoint, query_params=None, log_msg=""):
    """For requests which return paginated results"""
    query_params = query_params or {}
    resources = []
    page_num = 1
    while True:
        params = {"results-per-page": 100, "page": page_num}
        params.update(query_params)
        response = HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
            method=HttpMethod.GET,
            path=endpoint,
            params=params,
            msg="{} page {}".format(log_msg, page_num),
        )
        resources.extend(response["resources"])
        if page_num == response["total_pages"]:
            break
        page_num += 1
    return resources


# -------------------------------------------------- organizations --------------------------------------------------- #

def cf_api_get_orgs():
    """GET /v2/organizations"""
    return __get_all_pages(endpoint="organizations", log_msg="CF: get all organizations")


def cf_api_delete_org(org_guid):
    """DELETE /v2/organizations/{org_guid}"""
    ref_org_guid, _ = cf_get_ref_org_and_space_guids()
    if org_guid == ref_org_guid:
        raise YouMustBeJokingException("You're trying to delete {}".format(config.core_org_name))
    HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.DELETE,
        path="organizations/{}".format(org_guid),
        params={"recursive": "true", "async": "false"},
        msg="CF: delete organization",
    )


def cf_api_get_org_spaces(org_guid):
    """GET /v2/organizations/{org_guid}/spaces"""
    return __get_all_pages(endpoint="organizations/{}/spaces".format(org_guid), log_msg="CF: get spaces in org")


def cf_api_get_org_users(org_guid, space_guid=None):
    """GET /v2/organizations/{org_guid}/users"""
    params = {}
    if space_guid:
        params = {"space_guid": space_guid}
    return __get_all_pages(endpoint="organizations/{}/users".format(org_guid), query_params=params,
                           log_msg="CF: get users in org (space)")


# ------------------------------------------------------ spaces ------------------------------------------------------ #

def cf_api_get_spaces():
    """GET /v2/spaces"""
    return __get_all_pages(endpoint="spaces", log_msg="CF: get all spaces")


def cf_api_space_summary(space_guid):
    """GET /v2/spaces/{space_guid}/summary - Equal to running cf apps and cf services"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="spaces/{}/summary".format(space_guid),
        msg="CF: get space summary",
    )


def cf_api_delete_space(space_guid):
    """DELETE /v2/spaces/{space_guid}"""
    _, ref_space_guid = cf_get_ref_org_and_space_guids()
    if space_guid == ref_space_guid:
        raise YouMustBeJokingException("You're trying to delete {}".format(config.core_space_name))
    HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.DELETE,
        path="spaces/{}".format(space_guid),
        params={"recursive": "true", "async": "false"},
        msg="CF: delete space",
    )


def cf_api_get_space_routes(space_guid):
    """GET /v2/spaces/{space_guid}/routes"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="spaces/{}/routes".format(space_guid),
        msg="CF: get routes in space",
    )


# -------------------------------------------------- service --------------------------------------------------------- #


def cf_api_get_services(service_name=None):
    """GET /v2/services"""
    params = {}
    if service_name is not None:
        params["q"] = "label:{}".format(service_name)
    return __get_all_pages(endpoint="services", query_params=params, log_msg="CF: get all services")


# -------------------------------------------------- service plans --------------------------------------------------- #


def cf_api_update_service_access(service_guid, enable_service=True):
    """PUT /v2/service_plans/{service_guid}"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.PUT,
        path="service_plans/{}".format(service_guid),
        body={"public": enable_service},
        msg="CF: update service access",
    )


# ------------------------------------------------------ users ------------------------------------------------------- #

def cf_api_get_users():
    """GET /v2/users"""
    return __get_all_pages(endpoint="users", log_msg="CF: get all users")


def cf_api_delete_user(user_guid):
    """DELETE /v2/users/{user_guid}"""
    HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.DELETE,
        path="users/{}".format(user_guid),
        params={"async": "false"},
        msg="CF: delete user",
    )


# ------------------------------------------------ service instances ------------------------------------------------- #


def cf_api_create_user_provided_service_instance(instance_name, space_guid, credentials):
    """POST /v2/user_provided_service_instances"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.POST,
        path="user_provided_service_instances",
        body={"name": instance_name, "space_guid": space_guid, "credentials": credentials},
        msg="CF: create user provided service instance",
    )


def cf_api_get_user_provided_service_instances():
    """GET /v2/user_provided_service_instances"""
    return __get_all_pages("user_provided_service_instances", log_msg="CF: get upsi")


# ---------------------------------------------------- buildpacks ---------------------------------------------------- #


def cf_api_get_buildpacks():
    """GET /v2/buildpacks"""
    return __get_all_pages("buildpacks", log_msg="CF: get build packs")


# ------------------------------------------------------- apps ------------------------------------------------------- #


def cf_api_get_apps():
    """GET /v2/apps"""
    return __get_all_pages("apps", log_msg="CF: get apps")


def cf_api_get_app_env(app_guid):
    """GET /v2/apps/{app_guid}/env"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="apps/{}/env".format(app_guid),
        msg="CF: get app env",
    )


def cf_api_app_summary(app_guid):
    """GET /v2/apps/{app_guid}/summary"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="apps/{}/summary".format(app_guid),
        msg="CF: get app summary",
    )


def cf_api_delete_app(app_guid):
    """DELETE /v2/apps/{app_guid}"""
    HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.DELETE,
        path="apps/{}".format(app_guid),
        msg="CF: delete app",
    )


def cf_api_get_apps_bindings(app_guid):
    """GET /v2/apps/{app_guid}/service_bindings"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="apps/{}/service_bindings".format(app_guid),
        msg="CF: get service bindings",
    )

# ------------------------------------------------- service brokers -------------------------------------------------- #

def cf_api_get_service_brokers(space_guid=None):
    """GET /v2/service_brokers"""
    query_params = {}
    if space_guid is not None:
        query_params["space_guid"] = space_guid
    return __get_all_pages(endpoint="service_brokers", query_params=query_params,
                           log_msg="CF: get service brokers (in space)")


# ----------------------------------------------------- routes ------------------------------------------------------- #


def cf_api_delete_route(route_guid):
    """DELETE /v2/routes/{route_guid}"""
    HttpClientFactory.get(CloudFoundryConfigurationProvider.get()).request(
        method=HttpMethod.DELETE,
        path="routes/{}".format(route_guid),
        params={"async": "false"},
        msg="CF: delete route",
    )




# TODO rethink how this check is done

CORE_ORG_GUID = None
CORE_SPACE_GUID = None


def cf_get_ref_org_and_space_guids():
    """Return tuple of org_guid and space_guid for core org and space (e.g. trustedanalytics, platform)."""
    global CORE_ORG_GUID, CORE_SPACE_GUID
    if CORE_ORG_GUID is None or CORE_SPACE_GUID is None:
        orgs = cf_api_get_orgs()
        CORE_ORG_GUID = next(o["metadata"]["guid"] for o in orgs if o["entity"]["name"] == config.core_org_name)
        spaces = cf_api_get_org_spaces(CORE_ORG_GUID)
        CORE_SPACE_GUID = next(s["metadata"]["guid"] for s in spaces if s["entity"]["name"] == config.core_space_name)
    return CORE_ORG_GUID, CORE_SPACE_GUID
