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

from . import cloud_foundry as cf
from ..http_client.http_client_credentials import HttpClientCredentials
from ..http_client.http_client_type import HttpClientType
from ..constants import TapComponent


class ApplicationBrokerCredentialsProvider(object):
    """ Provide credentials for application broker http client. """

    _credentials = None

    @classmethod
    def get(cls) -> HttpClientCredentials:
        """ Return http credentials. """
        if cls._credentials is None:
            cls._provide_credentials()
        return cls._credentials

    @classmethod
    def _provide_credentials(cls):
        """ Retrieve credentials form application-broker environment variables. """
        response = cf.cf_api_get_apps()
        app_guid = None
        for app in response:
            if app["entity"]["name"] == TapComponent.application_broker.value:
                app_guid = app["metadata"]["guid"]
        app_broker_env = cf.cf_api_get_app_env(app_guid)
        cls._credentials = HttpClientCredentials(
            HttpClientType.APPLICATION_BROKER,
            app_broker_env["environment_json"]["AUTH_USER"],
            app_broker_env["environment_json"]["AUTH_PASS"]
        )
