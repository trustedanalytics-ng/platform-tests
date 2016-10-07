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

from modules.constants import ContainerBrokerHttpStatus, TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from tap_component_config import TAP_core_services


def _get_client():
    api_version = TAP_core_services[TapComponent.container_broker]["api_version"]
    configuration = K8sServiceConfigurationProvider.get(TapComponent.container_broker,
                                                        api_endpoint="api/{}".format(api_version))
    return HttpClientFactory.get(configuration)


def get_logs(*, instance_id):
    """ GET /service/{instanceId}/logs """
    response = _get_client().request(HttpMethod.GET,
                                     path="service/{}/logs".format(instance_id),
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get logs for instance")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def get_envs(*, instance_id):
    """ GET /service/{instanceId}/envs """
    response = _get_client().request(HttpMethod.GET,
                                     path="service/{}/envs".format(instance_id),
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get envs for instance")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def bind_service_instances(*, src_instance_id, dst_instance_id):
    """ POST /bind/{src_instance_id}/{dst_instance_id} """
    response = _get_client().request(HttpMethod.POST,
                                     path="bind/{}/{}".format(src_instance_id, dst_instance_id),
                                     msg="CONTAINER-BROKER: bind service instances")
    return response


def unbind_service_instances(*, src_instance_id, dst_instance_id):
    """ POST /unbind/{src_instance_id}/{dst_instance_id} """
    response = _get_client().request(HttpMethod.POST,
                                     path="unbind/{}/{}".format(src_instance_id, dst_instance_id),
                                     msg="CONTAINER-BROKER: unbind service instances")
    return response


def scale_service_instance(*, instance_id, replicas):
    """ PUT /scale/{instance_id} """
    body = {
        "replicas": replicas
    }
    response = _get_client().request(HttpMethod.PUT,
                                     path="scale/{}".format(instance_id),
                                     body=body,
                                     msg="CONTAINER-BROKER: scale service instance")
    return response

