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
from modules.http_client.configuration_provider.k8s_service import ProxiedConfigurationProvider


DEFAULT_NAMESPACE = "default"


def k8s_get_pods():
    """GET /namespaces/{namespace}/pods"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{DEFAULT_NAMESPACE}/pods",
        path_params={'DEFAULT_NAMESPACE': DEFAULT_NAMESPACE},
        msg="KUBERNETES: get pods"
    )


def k8s_get_nodes():
    """GET /nodes"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="nodes",
        msg="KUBERNETES: get nodes"
    )


def k8s_get_services(*, namespace=DEFAULT_NAMESPACE):
    """GET /namespaces/{namespace}/services"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{namespace}/services",
        path_params={'namespace': namespace},
        msg="KUBERNETES: get services"
    )


def k8s_get_service(service_name, *, namespace=DEFAULT_NAMESPACE):
    """GET /namespaces/{namespace}/services/{name}"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{namespace}/services/{service_name}",
        path_params={'namespace': namespace, 'service_name': service_name},
        msg="KUBERNETES: get service {}".format(service_name)
    )


def k8s_get_configmap(configmap_name):
    """GET /namespaces/{namespace}/configmaps/{configmap_name}"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{DEFAULT_NAMESPACE}/configmaps/{configmap_name}",
        path_params={'DEFAULT_NAMESPACE': DEFAULT_NAMESPACE, 'configmap_name': configmap_name},
        msg="KUBERNETES: get configmap {}".format(configmap_name)
    )


def k8s_logs(application_name, params):
    """GET /namespaces/{namespace}/pods/{application_name}/log"""
    return HttpClientFactory.get(KubernetesConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="namespaces/{DEFAULT_NAMESPACE}/pods/{application_name}/log",
        path_params={'DEFAULT_NAMESPACE': DEFAULT_NAMESPACE, 'application_name': application_name},
        params=params,
        msg="KUBERNETES: get logs {}".format(application_name)
    )


def k8s_get_pods_metrics(pod_ip_port):
    """This method does not call k8s api, but particular pod"""
    client = HttpClientFactory.get(ProxiedConfigurationProvider.get(url="https://{}".format(pod_ip_port)))
    return client.request(
        method=HttpMethod.GET,
        path="metrics",
        msg="POD: get metrics for {}".format(pod_ip_port)
    )


def k8s_scale_pod(pod_name, number_of_replicas, rest_prefix="apis", api_version="extensions/v1beta1"):
    """PUT /apis/extensions/v1beta1/namespaces/{namespace}/deployments/{name}/scale"""
    body = {
        "metadata": {
            "name": pod_name,
            "namespace": DEFAULT_NAMESPACE
        },
        "spec": {
            "replicas": number_of_replicas
        }
    }

    client = HttpClientFactory.get(KubernetesConfigurationProvider.get(rest_prefix, api_version))
    return client.request(
        method=HttpMethod.PUT,
        body=body,
        path="namespaces/{DEFAULT_NAMESPACE}/deployments/{pod_name}/scale",
        path_params={'DEFAULT_NAMESPACE': DEFAULT_NAMESPACE, 'pod_name': pod_name},
        msg="POD {} scaled to {} replicas".format(pod_name, number_of_replicas)
    )


def k8s_get_ingresses(rest_prefix="apis", api_version="extensions/v1beta1"):
    """PUT /apis/extensions/v1beta1/namespaces/{namespace}/ingresses"""
    client = HttpClientFactory.get(KubernetesConfigurationProvider.get(rest_prefix, api_version))
    return client.request(
        method=HttpMethod.GET,
        path="namespaces/{DEFAULT_NAMESPACE}/ingresses",
        path_params={'DEFAULT_NAMESPACE': DEFAULT_NAMESPACE},
        msg="KUBERNETES: get ingresses"
    )
