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

from .. import HttpClientConfiguration, HttpClientType, HttpClientFactory, HttpMethod


class ProxiedConfigurationProvider(object):
    _socks_proxy = "socks5://localhost:{}".format(config.ng_socks_proxy_port)

    @classmethod
    def _get_proxies(cls):
        return {"http": cls._socks_proxy, "https": cls._socks_proxy}

    @classmethod
    def get(cls, url):
        return HttpClientConfiguration(
            client_type=HttpClientType.BROKER,
            url=url,
            proxies=cls._get_proxies()
        )


class K8sServiceConfigurationProvider(ProxiedConfigurationProvider):
    _services = None

    @classmethod
    def _get_service_info(cls):
        socks_proxy = "socks5://localhost:{}".format(config.ng_socks_proxy_port)
        client_configuration = HttpClientConfiguration(
            client_type = HttpClientType.NO_AUTH,
            url="http://localhost:{}/api/{}".format(config.ng_kubernetes_api_port, config.ng_kubernetes_api_version),
            proxies={"http": socks_proxy, "https": socks_proxy})
        client = HttpClientFactory.get(client_configuration)
        response = client.request(
            method=HttpMethod.GET,
            path="namespaces/default/services",
            msg="KUBERNETES: get services")
        cls._services = {}
        for item in response["items"]:
            service_name = item["metadata"]["name"]
            service_host = item["spec"]["clusterIP"]
            service_port = item["spec"]["ports"][0]["port"]
            cls._services[service_name] = "{}:{}".format(service_host, service_port)

    @classmethod
    def get(cls, service_name=None, api_endpoint=None):
        if cls._services is None:
            cls._get_service_info()
        assert service_name in cls._services, "No service {}".format(service_name)
        credentials = config.ng_k8s_service_credentials()
        if api_endpoint is None:
            url = "http://{}".format(cls._services[service_name])
        else:
            url = "http://{}/{}".format(cls._services[service_name], api_endpoint)
        return HttpClientConfiguration(
            client_type=HttpClientType.BROKER,
            url=url,
            proxies=cls._get_proxies(),
            username=credentials[0],
            password=credentials[1]
        )


class ApiServiceConfigurationProvider():
    @classmethod
    def get(cls):
        return HttpClientConfiguration(
            client_type=HttpClientType.K8S_AS,
            url=config.api_url_full,
            username=config.admin_username,
            password=config.admin_password
        )
