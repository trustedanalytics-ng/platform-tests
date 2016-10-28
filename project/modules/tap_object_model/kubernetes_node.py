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

from modules.http_calls import kubernetes as kubernetes_api
from modules.http_client import HttpClientFactory, HttpMethod, HttpClientConfiguration, HttpClientType

class KubernetesNode(object):

    def __init__(self, name, ip, port):
        self.name = name
        self.host = "{}:{}".format(ip, port)

    def __repr__(self):
        return self.__class__.__name__

    @classmethod
    def get_list(cls):
        node_info = kubernetes_api.k8s_get_nodes()
        nodes = []
        for item in node_info["items"]:
            nodes.append(cls._from_response(item))
        return nodes

    @classmethod
    def _from_response(cls, response):
        return cls(name=response["metadata"]["name"], ip=response["status"]["addresses"][0]["address"],
                   port=response["status"]["daemonEndpoints"]["kubeletEndpoint"]["Port"])

    def get_metrics(self):
        proxy = "socks5://localhost:{}".format(config.ng_socks_proxy_port)
        configuration = HttpClientConfiguration(client_type=HttpClientType.NO_AUTH,
                                                url="https://{}".format(self.host),
                                                proxies={"http": proxy, "https": proxy})
        client = HttpClientFactory.get(configuration)
        response = client.request(method=HttpMethod.GET, path="metrics",
                                  msg="NODE: get metrics from {}".format(self.name))
        return response