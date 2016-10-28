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

from ..http_client_configuration import HttpClientConfiguration
from ..http_client_type import HttpClientType
from .base import BaseConfigurationProvider


class GrafanaConfigurationProvider(BaseConfigurationProvider):
    """Provide configuration for grafana http client."""

    @classmethod
    def get(cls, username=None, password=None) -> HttpClientConfiguration:
        """Provide http client configuration."""
        if username is None:
            username = config.admin_username
            password = config.admin_password
        return HttpClientConfiguration(
            client_type=HttpClientType.NO_AUTH,
            url=config.grafana_url,
            username=username,
            password=password
        )
