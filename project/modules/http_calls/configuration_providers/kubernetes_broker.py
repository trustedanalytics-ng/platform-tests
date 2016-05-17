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
from ...http_client.http_client_configuration import HttpClientConfiguration
from ...http_client.http_client_type import HttpClientType
from ...http_client.config import Config
from ...constants import TapComponent
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
        return Config.service_kubernetes_broker_basic_url()


class KubernetesBrokerTokenConfigurationProvider(BaseConfigurationProvider):
    """Provide configuration for cloud foundry http client."""

    @classmethod
    def provide_configuration(cls) -> HttpClientConfiguration:
        """Provide http client configuration."""
        return HttpClientConfiguration(
            HttpClientType.CLOUD_FOUNDRY,
            Config.service_kubernetes_broker_token_url(),
            CONFIG["admin_username"],
            CONFIG["admin_password"]
        )
