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

from modules.tap_object_model import K8sService
from .. import HttpClientConfiguration, HttpClientType
from tap_ng_component_config import k8s_core_services
from modules.constants import TapComponent


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
    def get(cls, service_name=None, api_endpoint=None):
        if cls._services is None:
            cls._services = K8sService.get_list()
        service = next((s for s in cls._services if s.name == service_name), None)
        assert service is not None, "No service {}".format(service_name)
        credentials = config.ng_k8s_service_credentials()
        if api_endpoint is None:
            url = service.url
        else:
            url = "{}/{}".format(service.url, api_endpoint)
        return HttpClientConfiguration(
            client_type=HttpClientType.BROKER,
            url=url,
            proxies=cls._get_proxies(),
            username=credentials[0],
            password=credentials[1]
        )


class ConsoleServiceConfigurationProvider(ProxiedConfigurationProvider):
    @classmethod
    def get(cls):
        api_version = k8s_core_services[TapComponent.console_service]["api_version"]
        configuration = K8sServiceConfigurationProvider.get(TapComponent.console_service,
                                                            api_endpoint="api/{}".format(api_version))
        return HttpClientConfiguration(
            client_type=HttpClientType.K8S_CS,
            url=configuration.url,
            proxies=cls._get_proxies(),
            username=configuration.username,
            password=configuration.password
        )
