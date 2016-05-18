#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License";
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

from .configuration_providers.kubernetes_broker import KubernetesBrokerConfigurationProvider
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.http_client_factory import HttpClientFactory


def k8s_broker_get_catalog():
    """GET /v$/catalog"""
    return HttpClientFactory.get(KubernetesBrokerConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="catalog",
        msg="K8S BROKER: get catalog"
    )


def k8s_broker_delete_service_instance(instance_guid):
    """DELETE /v$/service_instances/:instanceId"""
    return HttpClientFactory.get(KubernetesBrokerConfigurationProvider.get()).request(
        method=HttpMethod.DELETE,
        path="service_instances/{}".format(instance_guid),
        msg="K8S BROKER: delete service instance"
    )


def k8s_broker_create_service_offering(org_guid, space_guid, service_name=None):
    """PUT /v$/dynamicservice"""
    body = {
        "organization_guid": org_guid,
        "space_guid": space_guid,
        "parameters": None,
        "updateBroker": True,
        "dynamicService": {"serviceName": service_name, "planName": service_name}
    }
    return HttpClientFactory.get(KubernetesBrokerConfigurationProvider.get()).request(
        method=HttpMethod.PUT,
        path="dynamicservice",
        body=body,
        msg="K8S BROKER: create service offering"
    )
