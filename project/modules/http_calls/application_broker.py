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

from .app_broker_client import ApplicationBrokerClient


def app_broker_get_catalog():
    """GET /v$/catalog"""
    return ApplicationBrokerClient.get_client().request("GET", endpoint="catalog", log_msg="CF: get catalog")


def app_broker_create_service(app_guid, description, service_name):
    """POST /v$/catalog"""
    query = {
            "app": {
                "metadata": {"guid": app_guid }
            },
            "description": description,
            "name": service_name
        }
    return ApplicationBrokerClient.get_client().request("POST", endpoint="catalog", body=query,
                                                        log_msg="APP BROKER: create service in catalog")


def app_broker_delete_service(service_id):
    """DELETE /v$/catalog/:serviceId"""
    return ApplicationBrokerClient.get_client().request("DELETE",
                                                        endpoint="catalog/{}".format(service_id),
                                                        log_msg="APP BROKER: delete service")


def app_broker_new_service_instance(instance_guid, organization_guid, plan_id, service_id, space_guid, instance_name):
    """PUT /v$/service_instances/:instanceId"""
    query = {
            "organization_guid": organization_guid,
            "plan_id": plan_id,
            "service_id": service_id,
            "space_guid": space_guid,
            "parameters": {"name": instance_name}
        }
    return ApplicationBrokerClient.get_client().request("PUT",
                                                        endpoint="service_instances/{}".format(instance_guid),
                                                        body=query,
                                                        log_msg="APP BROKER: create new service instance")


def app_broker_delete_service_instance(instance_guid):
    """DELETE /v$/service_instances/:instanceId"""
    return ApplicationBrokerClient.get_client().request("DELETE",
                                                        endpoint="service_instances/{}".format(instance_guid),
                                                        log_msg="APP BROKER: delete service instance")


def app_broker_bind_service_instance(instance_guid, application_guid):
    """PUT /v$/service_instances/:instanceId/service_bindings/:app_guid"""
    return ApplicationBrokerClient.get_client().request("PUT",
                                                        endpoint="service_instances/{}/service_bindings/{}".format(instance_guid, application_guid),
                                                        log_msg="APP BROKER: bind service instance to app")
