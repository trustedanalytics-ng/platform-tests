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

from .http_client import HttpClient
from .http_client_type import HttpClientType
from .client_auth.client_auth_type import ClientAuthType
from .client_auth.client_auth_factory import ClientAuthFactory
from .http_client_configuration import HttpClientConfiguration


class HttpClientFactory(object):
    """Http client factory with implemented singleton behaviour for each generated client."""

    _INSTANCES = {}

    @classmethod
    def get(cls, configuration: HttpClientConfiguration) -> HttpClient:
        """Create http client for given configuration."""
        client_type = configuration.client_type

        if client_type == HttpClientType.UAA:
            return cls._get_instance(configuration, ClientAuthType.TOKEN_UAA)

        elif client_type == HttpClientType.CONSOLE:
            return cls._get_instance(configuration, ClientAuthType.LOGIN_PAGE)

        elif client_type == HttpClientType.CONSOLE_NO_AUTH:
            return cls._get_instance(configuration, ClientAuthType.NO_AUTH)

        elif client_type == HttpClientType.APPLICATION:
            return cls._get_instance(configuration, ClientAuthType.TOKEN_CF)

        elif client_type == HttpClientType.CLOUD_FOUNDRY:
            return cls._get_instance(configuration, ClientAuthType.TOKEN_CF)

        elif client_type == HttpClientType.BROKER:
            return cls._get_instance(configuration, ClientAuthType.HTTP_BASIC)

        elif client_type == HttpClientType.SERVICE_TOOL:
            return cls._get_instance(configuration, ClientAuthType.NO_AUTH)

        else:
            raise HttpClientFactoryInvalidClientTypeException(client_type)

    @classmethod
    def remove(cls, configuration: HttpClientConfiguration):
        """Remove client instance from cached instances."""
        if configuration.uid in cls._INSTANCES:
            del cls._INSTANCES[configuration.uid]

    @classmethod
    def _get_instance(cls, configuration, auth_type):
        """Check if there is already created requested client type and return it otherwise create new instance."""
        if configuration.uid in cls._INSTANCES:
            return cls._INSTANCES[configuration.uid]
        return cls._create_instance(configuration, auth_type)

    @classmethod
    def _create_instance(cls, configuration, auth_type):
        """Create new client instance."""
        auth = ClientAuthFactory.get(
            username=configuration.username,
            password=configuration.password,
            auth_type=auth_type
        )
        instance = HttpClient(configuration.url, auth)
        cls._INSTANCES[configuration.uid] = instance
        return instance


class HttpClientFactoryInvalidClientTypeException(Exception):
    TEMPLATE = "Http client with type {} is not implemented."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
