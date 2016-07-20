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
from modules.http_client import HttpClientConfiguration, HttpClientFactory, HttpClientType, HttpMethod


socks_proxy = "socks5://localhost:{}".format(config.ng_socks_proxy_port)
client_configuration = HttpClientConfiguration(
    client_type=HttpClientType.NO_AUTH,
    url="http://localhost:{}/api/{}".format(config.ng_kubernetes_api_port, config.ng_kubernetes_api_version),
    proxies={"http": socks_proxy, "https": socks_proxy}
)
client = HttpClientFactory.get(client_configuration)

default_namespace = "default"


def k8s_get_pods():
    """GET /namespaces/{namespace}/pods"""
    return client.request(
        method=HttpMethod.GET,
        path="namespaces/{}/pods".format(default_namespace),
        msg="KUBERNETES: get pods"
    )


def k8s_get_services():
    """GET /namespaces/{namespace}/services"""
    return client.request(
        method=HttpMethod.GET,
        path="namespaces/{}/services".format(default_namespace),
        msg="KUBERNETES: get services"
    )


def k8s_get_service(service_name):
    """GET /namespaces/{namespace}/services/{name}"""
    return client.request(
        method=HttpMethod.GET,
        path="namespaces/{}/services/{}".format(default_namespace, service_name),
        msg="KUBERNETES: get service {}".format(service_name)
    )

