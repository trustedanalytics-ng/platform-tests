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

from .base_provider import BaseConfigurationProvider
from modules.http_calls import cloud_foundry as cf
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_type import HttpClientType
from modules.http_client.config import Config
from modules.constants import TapComponent



class DemiurgeConfigurationProvider(BaseConfigurationProvider):
    """ Provide configuration for demiurge http client. """

    @classmethod
    def provide_configuration(cls):
        """Retrieve configuration form demiurge environment variables."""
        response = cf.cf_api_get_apps()
        app_guid = None
        for app in response:
            if app["entity"]["name"] == TapComponent.demiurge.value:
                app_guid = app["metadata"]["guid"]
        demiurge_env = cf.cf_api_get_app_env(app_guid)
        cls._configuration = HttpClientConfiguration(
            HttpClientType.BROKER,
            Config.service_demiurge_url(),
            demiurge_env["environment_json"]["USERNAME"],
            demiurge_env["environment_json"]["PASSWORD"]
        )
