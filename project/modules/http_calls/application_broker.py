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

from .application_broker_credentials_provider import ApplicationBrokerCredentialsProvider
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.http_client_factory import HttpClientFactory


def app_broker_get_catalog():
    """GET /v$/catalog"""
    return HttpClientFactory.get(ApplicationBrokerCredentialsProvider.get()).request(
        method=HttpMethod.GET,
        path="catalog",
        msg="APP BROKER: get catalog",
    )


def app_broker_create_service(app_guid, description, service_name):
    """POST /v$/catalog"""
    query = {
        "app": {
            "metadata": {"guid": app_guid}
        },
        "description": description,
        "name": service_name
    }
    return HttpClientFactory.get(ApplicationBrokerCredentialsProvider.get()).request(
        method=HttpMethod.POST,
        path="catalog",
        body=query,
        msg="APP BROKER: create service in catalog",
    )


def app_broker_delete_service(service_id):
    """DELETE /v$/catalog/:serviceId"""
    return HttpClientFactory.get(ApplicationBrokerCredentialsProvider.get()).request(
        method=HttpMethod.DELETE,
        path="catalog/{}".format(service_id),
        msg="APP BROKER: delete service",
    )


def app_broker_new_service_instance(instance_guid, organization_guid, plan_id, service_id, space_guid, instance_name):
    """PUT /v$/service_instances/:instanceId"""
    query = {
        "organization_guid": organization_guid,
        "plan_id": plan_id,
        "service_id": service_id,
        "space_guid": space_guid,
        "parameters": {"name": instance_name}
    }
    return HttpClientFactory.get(ApplicationBrokerCredentialsProvider.get()).request(
        method=HttpMethod.PUT,
        path="service_instances/{}".format(instance_guid),
        body=query,
        msg="APP BROKER: create new service instance",
    )


def app_broker_delete_service_instance(instance_guid):
    """DELETE /v$/service_instances/:instanceId"""
    return HttpClientFactory.get(ApplicationBrokerCredentialsProvider.get()).request(
        method=HttpMethod.DELETE,
        path="service_instances/{}".format(instance_guid),
        msg="APP BROKER: delete service instance",
    )


def app_broker_bind_service_instance(instance_guid, application_guid):
    """PUT /v$/service_instances/:instanceId/service_bindings/:app_guid"""
    return HttpClientFactory.get(ApplicationBrokerCredentialsProvider.get()).request(
        method=HttpMethod.PUT,
        path="service_instances/{}/service_bindings/{}".format(instance_guid, application_guid),
        msg="APP BROKER: bind service instance to app",
    )
