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
from modules.constants import TapComponent
from modules.http_calls import cloud_foundry as cf
from ..http_client_configuration import HttpClientConfiguration
from ..http_client_type import HttpClientType


class BrokerConfigurationProvider(object):
    default_username_env_key = "AUTH_USER"
    default_password_env_key = "AUTH_PASS"
    environment_json = "environment_json"
    http_client_type = HttpClientType.BROKER

    config = {
        TapComponent.application_broker: {
            "url": config.application_broker_url,
        },
        TapComponent.demiurge: {
            "url": config.demiurge_url,
            "username_env_key": "USERNAME",
            "password_env_key": "PASSWORD",
        },
        TapComponent.kubernetes_broker: {
            "url": "{}/{}".format(config.kubernetes_broker_url, config.cf_api_version),
        },
    }

    @classmethod
    def get(cls, broker_component: TapComponent) -> HttpClientConfiguration:
        """Provide http client configuration."""
        broker_config = cls.config.get(broker_component)
        assert broker_config is not None, "No configuration for {}".format(broker_component)
        cls._set_username_and_password(broker_component, broker_config)
        return HttpClientConfiguration(
            client_type=cls.http_client_type,
            url=broker_config["url"],
            username=broker_config["username"],
            password=broker_config["password"]
        )

    @classmethod
    def _get_environment(cls, broker_component: TapComponent):
        """Provide environment variables."""
        response = cf.cf_api_get_apps()
        app_guid = next((app["metadata"]["guid"] for app in response
                         if app["entity"]["name"] == broker_component), None)
        assert app_guid is not None, "No such app {}".format(broker_component)
        return cf.cf_api_get_app_env(app_guid)

    @classmethod
    def _set_username_and_password(cls, broker_component: TapComponent, broker_config: dict):
        username = broker_config.get("username")
        password = broker_config.get("password")
        if username is None or password is None:
            env = cls._get_environment(broker_component)[cls.environment_json]
            # save username and password in config for use in future requests
            broker_config["username"] = env[broker_config.get("username_env_key", cls.default_username_env_key)]
            broker_config["password"] = env[broker_config.get("password_env_key", cls.default_password_env_key)]
