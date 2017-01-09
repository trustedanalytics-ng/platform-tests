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

import os.path
import config

from .. import HttpClientFactory, HttpMethod
from .. import HttpClientConfiguration, HttpClientType
from .kubernetes import KubernetesConfigurationProvider

DEFAULT_NAMESPACE = "default"

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
        client = HttpClientFactory.get(KubernetesConfigurationProvider.get())
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

class K8sSecureServiceConfigurationProvider(KubernetesConfigurationProvider):
    """ Client configuration provider for services that require kubernetes certificates
    """
    _service_namespaces = {}

    @classmethod
    def _update_service_namespace_info(cls, namespace):
        client = HttpClientFactory.get(KubernetesConfigurationProvider.get())
        response = client.request(
            method=HttpMethod.GET,
            path="namespaces/{}/services".format(namespace),
            msg="KUBERNETES: get services in namespace {}".format(namespace))
        services = {}
        for item in response["items"]:
            service_name = item["metadata"]["name"]
            service_host = item["spec"]["clusterIP"]
            service_port = item["spec"]["ports"][0]["port"]
            services[service_name] = "{}:{}".format(service_host, service_port)
        cls._service_namespaces[namespace] = services

    @classmethod
    def get_service_url(cls, service_name, namespace=DEFAULT_NAMESPACE):
        if service_name not in cls._service_namespaces:
            cls._update_service_namespace_info(namespace)
        assert service_name in cls._service_namespaces[namespace],\
                "No service {} in kubernetes namespace {}".format(service_name, namespace)
        service_url = "https://{}".format(cls._service_namespaces[namespace][service_name])
        return service_url

    @classmethod
    def get(cls, service_url, rest_prefix="", api_version="v1"):
        """Specify either service_name, or service_addr_port"""
        if cls._kube_dir_path is None:
            cls._kube_dir_path = cls._download_config_directory()
            kube_config_path = os.path.join(cls._kube_dir_path, cls._KUBE_CONFIG_FILE_NAME)
            cls._certificate = cls._get_certificates(cls._kube_dir_path, kube_config_path)
        if api_version is not None:
            cls._api_version = api_version
        client_configuration = HttpClientConfiguration(
            client_type=HttpClientType.NO_AUTH,
            url="{}/{}/{}".format(service_url, rest_prefix, cls._api_version),
            proxies={"http": cls._SOCKS_PROXY, "https": cls._SOCKS_PROXY},
            cert=cls._certificate
        )
        return client_configuration


class ServiceConfigurationProvider:
    @classmethod
    def get(cls, url=config.api_url_full, username=config.admin_username, password=config.admin_password):
        return HttpClientConfiguration(
            client_type=HttpClientType.K8S_SERVICE,
            url=url,
            username=username,
            password=password
        )
