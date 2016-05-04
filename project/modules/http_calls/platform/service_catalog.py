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

from modules.api_client import PlatformApiClient


def api_get_marketplace_services(space_guid, client=None):
    """GET /rest/services"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/services", params={"space": space_guid},
                          log_msg="PLATFORM: get marketplace service list")


def api_get_service(service_guid, client=None):
    """GET /rest/service/{service_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/service/{}".format(service_guid), log_msg="PLATFORM: get service")


def api_get_service_instances(space_guid=None, service_guid=None, client=None):
    """GET /rest/service_instances"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {}
    if space_guid is not None:
        query_params["space"] = space_guid
    if service_guid is not None:
        query_params["broker"] = service_guid
    return client.request("GET", "rest/service_instances", params=query_params,
                          log_msg="PLATFORM: get service instance list")


def api_create_service_instance(name, service_plan_guid, org_guid, space_guid, params=None, client=None):
    """POST /rest/service_instances"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "name": name,
        "organization_guid": org_guid,
        "service_plan_guid": service_plan_guid,
        "space_guid": space_guid,
        "parameters": {"name": name}
    }
    if params is not None:
        body["parameters"].update(params)
    return client.request("POST", "rest/service_instances", body=body, log_msg="PLATFORM: create service instance")


def api_delete_service_instance(service_instance_guid, client):
    """DELETE /rest/service_instances/{service_instance_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/service_instances/{}".format(service_instance_guid),
                          log_msg="PLATFORM: delete service instance")


def api_get_service_plans(service_type_label, client):
    """GET /rest/services/{service_type_label}/service_plans"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/services/{}/service_plans".format(service_type_label),
                          log_msg="PLATFORM: get service plans")


def api_get_service_instances_summary(space_guid=None, service_keys=True, client=None):
    """GET /rest/service_instances/summary"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {}
    if space_guid:
        query_params["space"] = space_guid
    if service_keys:
        query_params["service_keys"] = service_keys
    return client.request("GET", "rest/service_instances/summary", params=query_params,
                          log_msg="PLATFORM: get service instances summary")


def api_create_service_key(service_instance_guid, service_key_name, client=None):
    """POST /rest/service_keys"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "name": service_key_name,
        "service_instance_guid": service_instance_guid
    }
    return client.request(method="POST", endpoint="rest/service_keys", body=body,
                          log_msg="Platform: create service key")


def api_delete_service_key(service_key_guid, client=None):
    """DELETE /rest/service_keys/{service_key_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request(method="DELETE", endpoint="rest/service_keys/{}".format(service_key_guid),
                          log_msg="Platform: delete service key")


def api_get_filtered_applications(space, service_label=None, client=None):
    """GET /rest/apps"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {"space": space}
    if service_label is not None:
        query_params["service_label"] = service_label
    return client.request("GET", "rest/apps", params=query_params, log_msg="PLATFORM: get application list")


def api_get_app_summary(app_guid, client=None):
    """GET /rest/apps/{app_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/apps/{}".format(app_guid), log_msg="PLATFORM: get application summary")


def api_delete_app(app_guid, client=None):
    """DELETE /rest/apps/{app_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/apps/{}".format(app_guid), log_msg="PLATFORM: delete application")


def api_change_app_status(app_guid, status, client=None):
    """POST /rest/apps/{app_guid}/status"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/apps/{}/status".format(app_guid), body={"state": status},
                          log_msg="PLATFORM: restage app")


def api_get_app_bindings(app_guid, client=None):
    """GET /rest/apps/{app_guid}/service_bindings"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/apps/{}/service_bindings".format(app_guid),
                              log_msg="PLATFORM: get app bindings")
    return response["resources"]


def api_create_service_binding(app_guid, service_instance_guid, client=None):
    """POST /rest/apps/{app_guid}/service_bindings"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/apps/{}/service_bindings".format(app_guid),
                          body={"service_instance_guid": service_instance_guid},
                          log_msg="PLATFORM: Create binding for app and service")

def api_delete_service_binding(binding_guid, client=None):
    """DELETE /rest/service_bindings/{binding_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/service_bindings/{}".format(binding_guid), log_msg="PLATFORM: delete binding")



