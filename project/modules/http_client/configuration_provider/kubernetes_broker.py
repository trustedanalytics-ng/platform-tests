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

from configuration.config import CONFIG
from ...constants import TapComponent
from ..http_client_configuration import HttpClientConfiguration
from ..http_client_type import HttpClientType
from ..config import Config as ClientConfig
from .base_broker import BaseBrokerConfigurationProvider
from .base import BaseConfigurationProvider


# noinspection PyAbstractClass
class KubernetesBrokerBasicConfigurationProvider(BaseBrokerConfigurationProvider):
    """Provide configuration for kubernetes broker http client."""

    @classmethod
    def tap_component(cls) -> TapComponent:
        """Provide tap component."""
        return TapComponent.kubernetes_broker

    @classmethod
    def http_client_type(cls) -> HttpClientType:
        """Provide http client type."""
        return HttpClientType.BROKER

    @classmethod
    def http_client_url(cls) -> str:
        """Provide http client url."""
        return ClientConfig.service_kubernetes_broker_basic_url()


class KubernetesBrokerTokenConfigurationProvider(BaseConfigurationProvider):
    """Provide configuration for cloud foundry http client."""

    @classmethod
    def provide_configuration(cls, username=None, password=None) -> HttpClientConfiguration:
        """Provide http client configuration."""
        if username is None:
            username = CONFIG["admin_username"]
            password = CONFIG["admin_password"]
        return HttpClientConfiguration(
            HttpClientType.CLOUD_FOUNDRY,
            ClientConfig.service_kubernetes_broker_token_url(),
            username,
            password
        )
