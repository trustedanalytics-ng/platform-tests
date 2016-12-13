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

from .base_configuration import BaseConfiguration
from project.modules.remote_logger.config import Config
from ..http_client.http_client_factory import HttpClientFactory
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.configuration_provider.kubernetes import KubernetesConfigurationProvider


class LogProviderConfiguration(BaseConfiguration):
    """Log provider configuration object."""

    ELASTIC_KIBANA = "elastic-kibana"

    def __init__(self, from_date, to_date, app_name):
        super().__init__(from_date, to_date)
        self._validate("app_name", str, app_name)
        self.__app_name = app_name
        Config.ELASTIC_SEARCH_HOST = self.get_elastic_kibana_ip()

    @property
    def app_name(self):
        """Application name."""
        return self.__app_name

    @classmethod
    def get_elastic_kibana_ip(cls):
        client = HttpClientFactory.get(KubernetesConfigurationProvider.get())

        response = client.request(
            method=HttpMethod.GET,
            path="namespaces/kube-system/services")

        for item in response["items"]:
            if item["metadata"]["name"] == cls.ELASTIC_KIBANA:
                return item["spec"]["clusterIP"]
        return ''

