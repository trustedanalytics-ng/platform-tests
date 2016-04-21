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

from .config import Config
from .http_client import HttpClient
from .http_client_type import HttpClientType
from .client_auth.client_auth_type import ClientAuthType
from .client_auth.client_auth_factory import ClientAuthFactory
from .http_client_credentials import HttpClientCredentials


class HttpClientFactory(object):
    """Http client factory with implemented singleton behaviour for each generated client."""

    _INSTANCES = {}

    @classmethod
    def get(cls, credentials: HttpClientCredentials) -> HttpClient:
        """Create http client for given type and user credentials."""
        client_type = credentials.client_type

        if client_type == HttpClientType.UAA:
            return cls._get_instance(credentials, Config.service_uaa_url(), ClientAuthType.TOKEN_UAA)

        elif client_type == HttpClientType.CONSOLE:
            return cls._get_instance(credentials, Config.service_console_url(), ClientAuthType.LOGIN_PAGE)

        elif client_type == HttpClientType.PLATFORM:
            return cls._get_instance(credentials, Config.service_platform_url(), ClientAuthType.TOKEN_BASIC)

        elif client_type == HttpClientType.CLOUD_FOUNDRY:
            return cls._get_instance(credentials, Config.service_cloud_foundry_url(), ClientAuthType.TOKEN_BASIC)

        elif client_type == HttpClientType.APPLICATION_BROKER:
            return cls._get_instance(credentials, Config.service_application_broker_url(), ClientAuthType.HTTP_BASIC)

        else:
            raise HttpClientFactoryInvalidClientTypeException(client_type)

    @classmethod
    def _get_instance(cls, credentials, client_url, auth_type):
        """Check if there is already created requested client type and return it otherwise create new instance."""
        if credentials.uid in cls._INSTANCES:
            return cls._INSTANCES[credentials.uid]
        return cls._create_instance(credentials, client_url, auth_type)

    @classmethod
    def _create_instance(cls, credentials, client_url, auth_type):
        """Create new client instance."""
        auth = ClientAuthFactory.get(
            username=credentials.username,
            password=credentials.password,
            auth_type=auth_type
        )
        instance = HttpClient(client_url, auth)
        cls._INSTANCES[credentials.uid] = instance
        return instance


class HttpClientFactoryInvalidClientTypeException(Exception):
    TEMPLATE = "Http client with type {} is not implemented."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
