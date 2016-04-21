#
# Copyright (c) 2015-2016 Intel Corporation
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

from requests.auth import HTTPBasicAuth

from configuration import config
from ..api_client import PlatformApiClient
from ..http_calls import cloud_foundry as cf


class ApplicationBrokerClient(PlatformApiClient):
    """HTTP client for application-broker api calls. Uses basic authentication."""

    _APPLICATION_BROKER_CLIENT = None
    _auth = None

    def __init__(self, platform_username, platform_password):
        super().__init__(platform_username, platform_password)

    @property
    def url(self):
        return "http://application-broker.{}/{}/".format(config.CONFIG["domain"], config.CONFIG["cf_api_version"])

    @classmethod
    def get_client(cls):
        if cls._APPLICATION_BROKER_CLIENT is None:
            response = cf.cf_api_get_apps()
            app_guid = None
            for app in response:
                if app["entity"]["name"] == "application-broker":
                    app_guid = app["metadata"]["guid"]
            app_broker_env = cf.cf_api_get_app_env(app_guid)

            admin_username = app_broker_env["environment_json"]["AUTH_USER"]
            admin_password = app_broker_env["environment_json"]["AUTH_PASS"]
            cls._auth = HTTPBasicAuth(admin_username,admin_password)
            cls._APPLICATION_BROKER_CLIENT = cls(admin_username, admin_password)
        return cls._APPLICATION_BROKER_CLIENT

    def request(self, method, endpoint, headers=None, files=None, params=None, data=None, body=None, log_msg=""):
        auth = self._auth
        return super().request(method, endpoint, headers, files, params, data, body, log_msg, auth)