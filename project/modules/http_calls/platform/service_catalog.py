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

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.http_client_factory import HttpClientFactory
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider


def api_get_marketplace_services(space_guid, client=None):
    """GET /rest/services"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/services",
        params={"space": space_guid},
        msg="PLATFORM: get marketplace service list"
    )


def api_get_service(service_guid, client=None):
    """GET /rest/service/{service_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/services/{}".format(service_guid),
        msg="PLATFORM: get service"
    )


def api_create_service(name, description, org_guid, app_name, app_guid, image=None, display_name=None, tags=None,
                       client=None):
    """GET /rest/marketplace/application"""
    metadata = {}
    if image is not None:
        metadata["imageUrl"] = image
    if display_name is not None:
        metadata["displayName"] = display_name
    body = {
        "app": {
            "metadata": {
                "guid": app_guid
            }
        },
        "creator_info": {
            "creator_guid": app_guid,
            "creator_name": app_name
        },
        "name": name,
        "description": description,
        "metadata": metadata,
        "org_guid": org_guid,
        "tags": [] if tags is None else tags
    }
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="rest/marketplace/application",
        body=body,
        msg="PLATFORM: create service"
    )


def api_delete_service(service_guid, client=None):
    """DELETE /rest/services/{service_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="rest/services/{}".format(service_guid),
        msg="PLATFORM: delete service"
    )


def api_get_service_instances(space_guid=None, service_guid=None, client=None):
    """GET /rest/service_instances"""
    query_params = {}
    if space_guid is not None:
        query_params["space"] = space_guid
    if service_guid is not None:
        query_params["broker"] = service_guid

    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/service_instances",
        params=query_params,
        msg="PLATFORM: get service instance list"
    )


def api_create_service_instance(name, service_plan_guid, org_guid, space_guid, params=None, client=None):
    """POST /rest/service_instances"""
    body = {
        "name": name,
        "organization_guid": org_guid,
        "service_plan_guid": service_plan_guid,
        "space_guid": space_guid,
        "parameters": {"name": name},
    }
    if params is not None:
        body["parameters"].update(params)
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="rest/service_instances",
        body=body,
        msg="PLATFORM: create service instance"
    )


def api_delete_service_instance(service_instance_guid, client):
    """DELETE /rest/service_instances/{service_instance_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="rest/service_instances/{}".format(service_instance_guid),
        msg="PLATFORM: delete service instance"
    )


def api_get_service_plans(service_type_label, client):
    """GET /rest/services/{service_type_label}/service_plans"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/services/{}/service_plans".format(service_type_label),
        msg="PLATFORM: get service plans"
    )


def api_get_service_instances_summary(space_guid=None, service_keys=True, client=None):
    """GET /rest/service_instances/summary"""
    query_params = {}
    if space_guid:
        query_params["space"] = space_guid
    if service_keys:
        query_params["service_keys"] = service_keys
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/service_instances/summary",
        params=query_params,
        msg="PLATFORM: get service instances summary"
    )


def api_create_service_key(service_instance_guid, service_key_name, client=None):
    """POST /rest/service_keys"""
    body = {
        "name": service_key_name,
        "service_instance_guid": service_instance_guid,
    }
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="rest/service_keys",
        body=body,
        msg="PLATFORM: create service key"
    )


def api_delete_service_key(service_key_guid, client=None):
    """DELETE /rest/service_keys/{service_key_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="rest/service_keys/{}".format(service_key_guid),
        msg="PLATFORM: delete service key"
    )


def api_get_filtered_applications(space, service_label=None, client=None):
    """GET /rest/apps"""
    query_params = {"space": space}
    if service_label is not None:
        query_params["service_label"] = service_label
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/apps",
        params=query_params,
        msg="PLATFORM: get application list"
    )


def api_get_app_summary(app_guid, client=None):
    """GET /rest/apps/{app_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/apps/{}".format(app_guid),
        msg="PLATFORM: get application summary"
    )


def api_delete_app(app_guid, cascade=False, client=None):
    """DELETE /rest/apps/{app_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    params = {}
    if cascade:
        params["cascade"] = "true"
    return client.request(
        method=HttpMethod.DELETE,
        path="rest/apps/{}".format(app_guid),
        params=params,
        msg="PLATFORM: delete application"
    )


def api_change_app_status(app_guid, status, client=None):
    """POST /rest/apps/{app_guid}/status"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="rest/apps/{}/status".format(app_guid),
        body={"state": status},
        msg="PLATFORM: restage application"
    )


def api_get_app_bindings(app_guid, client=None):
    """GET /rest/apps/{app_guid}/service_bindings"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    response = client.request(
        method=HttpMethod.GET,
        path="rest/apps/{}/service_bindings".format(app_guid),
        msg="PLATFORM: get application bindings"
    )
    return response["resources"]


def api_create_service_binding(app_guid, service_instance_guid, client=None):
    """POST /rest/apps/{app_guid}/service_bindings"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="rest/apps/{}/service_bindings".format(app_guid),
        body={"service_instance_guid": service_instance_guid},
        msg="PLATFORM: Create binding for app and service"
    )


def api_delete_service_binding(binding_guid, client=None):
    """DELETE /rest/service_bindings/{binding_guid}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="rest/service_bindings/{}".format(binding_guid),
        msg="PLATFORM: delete binding"
    )


