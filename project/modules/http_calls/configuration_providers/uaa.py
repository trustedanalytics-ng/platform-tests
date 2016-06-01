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

from ...constants import TapComponent
from ...tap_object_model import Application
from ...http_client.http_client_configuration import HttpClientConfiguration
from ...http_client.http_client_type import HttpClientType
from ...http_client.config import Config as ClientConfig
from .base import BaseConfigurationProvider


class UaaConfigurationProvider(BaseConfigurationProvider):
    """Provide configuration for UAA http client."""

    @classmethod
    def provide_configuration(cls, username=None, password=None) -> HttpClientConfiguration:
        """Provide http client configuration."""
        if username is None:
            sso = cls._get_sso()
            username = sso["credentials"]["clientId"]
            password = sso["credentials"]["clientSecret"]
        return HttpClientConfiguration(
            client_type=HttpClientType.UAA,
            url=ClientConfig.service_uaa_url(),
            username=username,
            password=password
        )

    @classmethod
    def _get_sso(cls):
        """Provide sso environment variable."""
        apps = Application.cf_api_get_list()
        user_management = next(a for a in apps if a.name == TapComponent.user_management.value)
        user_management_env = user_management.cf_api_env()
        upsi = user_management_env["VCAP_SERVICES"]["user-provided"]
        return next(x for x in upsi if x["name"] == "sso")
