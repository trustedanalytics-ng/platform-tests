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
                                     path="service/{instance_id}/logs",
                                     path_params={'instance_id': instance_id},
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get logs for instance")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def get_envs(*, instance_id):
    """ GET /service/{instanceId}/credentials """
    response = _get_client().request(HttpMethod.GET,
                                     path="service/{instance_id}/credentials",
                                     path_params={'instance_id': instance_id},
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get envs for instance")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def bind_service_instances(*, src_instance_id, dst_instance_id):
    """ POST /bind/{src_instance_id}/{dst_instance_id} """
    response = _get_client().request(HttpMethod.POST,
                                     path="bind/{src_instance_id}/{dst_instance_id}",
                                     path_params={'src_instance_id': src_instance_id,
                                                  'dst_instance_id': dst_instance_id},
                                     msg="CONTAINER-BROKER: bind service instances")
    return response


def unbind_service_instances(*, src_instance_id, dst_instance_id):
    """ POST /unbind/{src_instance_id}/{dst_instance_id} """
    response = _get_client().request(HttpMethod.POST,
                                     path="unbind/{src_instance_id}/{dst_instance_id}",
                                     path_params={'src_instance_id': src_instance_id,
                                                  'dst_instance_id': dst_instance_id},
                                     msg="CONTAINER-BROKER: unbind service instances")
    return response


def scale_service_instance(*, instance_id, replicas):
    """ PUT /scale/{instance_id} """
    body = {
        "replicas": replicas
    }
    response = _get_client().request(HttpMethod.PUT,
                                     path="scale/{instance_id}",
                                     path_params={'instance_id': instance_id},
                                     body=body,
                                     msg="CONTAINER-BROKER: scale service instance")
    return response


def get_core_components_version():
    """ GET /deployment/core/versions """
    response = _get_client().request(HttpMethod.GET,
                                     path="deployment/core/versions",
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get core components version")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def get_secret(*, secret_name):
    """ GET /secret/{secret_name} """
    response = _get_client().request(HttpMethod.GET,
                                     path="secret/{secret_name}",
                                     path_params={'secret_name': secret_name},
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get secret")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def get_configmap(*, configmap_name):
    """ GET /configmap/{configmap_name} """
    response = _get_client().request(HttpMethod.GET,
                                     path="configmap/{configmap_name}",
                                     path_params={'configmap_name': configmap_name},
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get configmap")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()


def expose_service_instance(*, instance_id, hostname, ports: list, body=None):
    """ POST /service/{instance_id}/expose """
    if body is None:
        body = {
            "hostname": hostname,
            "ports": ports
        }
    response = _get_client().request(HttpMethod.POST,
                                     path="service/{instance_id}/expose",
                                     path_params={'instance_id': instance_id},
                                     body=body,
                                     msg="CONTAINER-BROKER: expose service instance")
    return response


def unexpose_service_instance(*, instance_id):
    """ DELETE /service/{instance_id}/expose """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="service/{instance_id}/expose",
                                     path_params={'instance_id': instance_id},
                                     msg="CONTAINER-BROKER: unexpose service instance")
    return response


def get_hosts(*, instance_id):
    """ GET /service/{instance_id}/hosts """
    response = _get_client().request(HttpMethod.GET,
                                     path="service/{instance_id}/hosts",
                                     path_params={'instance_id': instance_id},
                                     raw_response=True,
                                     msg="CONTAINER-BROKER: get hosts")
    assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
    return response.json()
