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

from retry import retry
from requests import ConnectionError

from modules.constants import HttpStatus
from modules.http_calls import kubernetes as kubernetes_api
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from modules.http_client import HttpClientFactory, HttpMethod
from modules.tap_object_model.kubernetes_ingress import KubernetesIngress
from tap_component_config import TAP_core_services


class KubernetesPod(object):
    RUNNING = "Running"

    def __init__(self, name, state, nodes, instance_id_label=None, containers=None, envs=None):
        self.name = name
        self.state = state
        self.instance_id_label = instance_id_label
        self.containers = containers
        self.nodes = nodes
        self.envs = envs

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    @classmethod
    def get_list(cls):
        response = kubernetes_api.k8s_get_pods()
        pods = []
        for item in response["items"]:
            pod = cls._from_response(item)
            pods.append(pod)
        return pods

    @classmethod
    def get_from_tap_app_name(cls, tap_app_name):
        ingress = KubernetesIngress.get_ingress_by_tap_name(tap_app_name)
        pods = KubernetesPod.get_list()
        return next((i for i in pods if i.name.startswith(ingress.name)))

    @classmethod
    def _from_response(cls, response):
        node_list = [response["spec"]["nodeName"]]  # Currently each pod is run on one node

        envs = {}
        for container in response["spec"]["containers"]:
            for pair in container.get("env", []):
                envs[pair["name"]] = pair.get("value", pair.get("valueFrom"))

        return cls(name=response["metadata"]["name"], state=response["status"]["phase"], nodes=node_list,
                   instance_id_label=response["metadata"].get("labels", {}).get("instance_id"),
                   containers=response["spec"].get("containers"), envs=envs)

    def get_client(self, service_name, endpoint=None):
        configuration = K8sServiceConfigurationProvider.get(service_name, api_endpoint=endpoint)
        return HttpClientFactory.get(configuration)

    @retry(AssertionError, tries=50, delay=3)
    def ensure_pod_terminated(self):
        pod = next((pod for pod in self.get_list() if pod.name == self.name), None)
        assert pod is None

    @retry(AssertionError, tries=50, delay=3)
    def ensure_pod_state(self, state):
        pod_name_prefix = "-".join(self.name.split("-")[:-2])  # after restart POD's name has changed
        pod = next((pod for pod in self.get_list() if pod.name.startswith(pod_name_prefix)), None)
        assert pod is not None and pod.state == state

    def restart_pod(self):
        pod_name_prefix = "-".join(self.name.split("-")[:-2])
        number_of_replicas = 0
        kubernetes_api.k8s_scale_pod(pod_name_prefix, number_of_replicas)
        self.ensure_pod_terminated()
        number_of_replicas = 1
        kubernetes_api.k8s_scale_pod(pod_name_prefix, number_of_replicas)
        self.ensure_pod_state(self.RUNNING)

    @retry(ConnectionError, tries=50, delay=3)
    def ensure_pod_in_good_health(self):
        pod_name_prefix = "-".join(self.name.split("-")[:-2])
        try:
            TAP_core_service = TAP_core_services[pod_name_prefix]
        except KeyError:
            TAP_core_service = None
        assert TAP_core_service is not None, "POD {} doesn't exist or is not a core service".format(pod_name_prefix)
        health_client = self.get_client(pod_name_prefix)
        response = health_client.request(HttpMethod.GET,
                                         path=TAP_core_service["health_endpoint"],
                                         raw_response=True,
                                         raise_exception=True,
                                         msg="get healthz")
        assert response.status_code == HttpStatus.CODE_OK

    def get_bindings(self):
        """You have to restage the app after binding/unbinding a service."""
        bindings = []
        for name, value in self.envs.items():
            if name.startswith("SERVICES_BOUND_"):
                bindings.append(value)
        return bindings
