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
from .base import BaseConfigurationProvider


class CloudFoundryConfigurationProvider(BaseConfigurationProvider):
    """Provide configuration for cloud foundry http client."""

    @classmethod
    def provide_configuration(cls) -> HttpClientConfiguration:
        """Provide http client configuration."""
        return HttpClientConfiguration(
            HttpClientType.CLOUD_FOUNDRY,
            Config.service_cloud_foundry_url(),
            CONFIG["admin_username"],
            CONFIG["admin_password"]
        )
