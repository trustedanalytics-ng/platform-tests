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

from .. import cloud_foundry as cf
from ...http_client.http_client_configuration import HttpClientConfiguration
from ...http_client.http_client_type import HttpClientType
from ...http_client.config import Config
from ...constants import TapComponent
from .base_provider import BaseConfigurationProvider


class KubernetesBrokerConfigurationProvider(BaseConfigurationProvider):
    """Provide configuration for kubernetes broker http client."""

    @classmethod
    def provide_configuration(cls):
        """Retrieve configuration form kubernetes-broker environment variables."""
        response = cf.cf_api_get_apps()
        app_guid = None
        for app in response:
            if app["entity"]["name"] == TapComponent.kubernetes_broker.value:
                app_guid = app["metadata"]["guid"]
        kubernetes_broker_env = cf.cf_api_get_app_env(app_guid)
        cls._configuration = HttpClientConfiguration(
            HttpClientType.KUBERNETES_BROKER,
            Config.service_kubernetes_broker_url(),
            kubernetes_broker_env["environment_json"]["AUTH_USER"],
            kubernetes_broker_env["environment_json"]["AUTH_PASS"]
        )
