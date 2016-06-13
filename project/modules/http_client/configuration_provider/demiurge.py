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

from .base_broker import BaseBrokerConfigurationProvider
from ...constants import TapComponent
from ..http_client_type import HttpClientType
from ..config import Config as ClientConfig


# noinspection PyAbstractClass
class DemiurgeConfigurationProvider(BaseBrokerConfigurationProvider):
    """ Provide configuration for demiurge http client. """
    username_env_key = "USERNAME"
    password_env_key = "PASSWORD"

    @classmethod
    def tap_component(cls) -> TapComponent:
        """Provide tap component."""
        return TapComponent.demiurge

    @classmethod
    def http_client_type(cls) -> HttpClientType:
        """Provide http client type."""
        return HttpClientType.BROKER

    @classmethod
    def http_client_url(cls) -> str:
        """Provide http client url."""
        return ClientConfig.service_demiurge_url()
