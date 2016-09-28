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

from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.kubernetes import KubernetesConfigurationProvider


DEFAULT_NAMESPACE = "default"


def k8s_get_pods():
    """GET /namespaces/{namespace}/pods"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{}/pods".format(DEFAULT_NAMESPACE),
        msg="KUBERNETES: get pods"
    )


def k8s_get_services():
    """GET /namespaces/{namespace}/services"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{}/services".format(DEFAULT_NAMESPACE),
        msg="KUBERNETES: get services"
    )


def k8s_get_service(service_name):
    """GET /namespaces/{namespace}/services/{name}"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{}/services/{}".format(DEFAULT_NAMESPACE, service_name),
        msg="KUBERNETES: get service {}".format(service_name)
    )


def k8s_get_configmap(configmap_name):
    """GET /namespaces/{namespace}/configmaps/{configmap_name}"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{}/configmaps/{}".format(DEFAULT_NAMESPACE, configmap_name),
        msg="KUBERNETES: get configmap {}".format(configmap_name)
    )

