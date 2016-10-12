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
from modules.constants import TapComponent
from modules.http_client.configuration_provider.cloud_foundry import CloudFoundryConfigurationProvider
from modules.http_client.configuration_provider.broker import BrokerConfigurationProvider
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client_factory import HttpClientFactory


def k8s_broker_get_service_status(org_guid, service_id):
    """GET /v$/:org_id/service/:instance_id/status"""
    return HttpClientFactory.get(BrokerConfigurationProvider.get(TapComponent.kubernetes_broker)).request(
        method=HttpMethod.GET,
        path="{}/service/{}/status".format(org_guid, service_id),
        msg="K8S BROKER: get instance status"
    )


def k8s_broker_change_instance_visibility(org_guid, space_guid, plan_id, service_id, visibility=None):
    """POST /rest/kubernetes/service/visibility"""
    body = {
        "organization_guid": org_guid,
        "plan_id": plan_id,
        "service_id": service_id,
        "space_guid": space_guid,
        "visibility": visibility
    }

    response = HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.POST,
        path="rest/kubernetes/service/visibility",
        body=body,
        msg="K8S BROKER: change instance visibility"
    )
    return response


def k8s_broker_get_instance(org_guid, space_guid, service_id):
    """GET /rest/kubernetes/{org_guid}/{space_guid}/service/{service_instance_guid}"""
    response = HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.GET,
        path="rest/kubernetes/{}/{}/service/{}".format(org_guid, space_guid, service_id),
        msg="K8S BROKER: get instance"
    )
    return response


def k8s_broker_get_instance_list(org_guid, space_guid):
    """GET /rest/kubernetes/{org_guid}/{space_guid}/services"""
    response = HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.GET,
        path="rest/kubernetes/{}/{}/services".format(org_guid, space_guid),
        msg="K8S BROKER: get instance list"
    )
    return response


def k8s_broker_delete_instance(instance_guid):
    """DELETE /v$/service_instances/:instanceId"""
    return HttpClientFactory.get(BrokerConfigurationProvider.get(TapComponent.kubernetes_broker)).request(
        method=HttpMethod.DELETE,
        path="service_instances/{}".format(instance_guid),
        msg="K8S BROKER: delete instance"
    )


def k8s_broker_create_secret(org_guid, key_id, username_b64, password_b64):
    """POST /rest/kubernetes/{org_id}/secret/{key}"""
    body = {
        "apiVersion": "v1",
        "data": {"username": username_b64, "password": password_b64},
        "kind": "Secret",
        "metadata": {"name": key_id, "labels": {"managed_by": "TAP"}}
    }
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.POST,
        body=body,
        path="rest/kubernetes/{}/secret/{}".format(org_guid, key_id),
        msg="K8S BROKER: create secret"
    )


def k8s_broker_get_secret(org_guid, key_id):
    """GET /rest/kubernetes/{org_id}/secret/{key}"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.GET,
        path="rest/kubernetes/{}/secret/{}".format(org_guid, key_id),
        msg="K8S BROKER: get secret"
    )


def k8s_broker_update_secret(org_guid, key_id, username_b64=None, password_b64=None):
    """PUT /rest/kubernetes/{org_id}/secret/{key}"""
    body = {
        "data": {},
        "metadata": {"name": key_id, "labels": {"managed_by": "TAP"}}
    }
    if username_b64 is not None:
        body["data"]["username"] = username_b64
    if password_b64 is not None:
        body["data"]["password"] = password_b64

    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.PUT,
        body=body,
        path="rest/kubernetes/{}/secret/{}".format(org_guid, key_id),
        msg="K8S BROKER: update secret"
    )


def k8s_broker_delete_secret(org_guid, key_id):
    """DELETE /rest/kubernetes/{org_id}/secret/{key}"""
    return HttpClientFactory.get(CloudFoundryConfigurationProvider.get(url=config.kubernetes_broker_url)).request(
        method=HttpMethod.DELETE,
        path="rest/kubernetes/{}/secret/{}".format(org_guid, key_id),
        msg="K8S BROKER: delete secret"
    )
