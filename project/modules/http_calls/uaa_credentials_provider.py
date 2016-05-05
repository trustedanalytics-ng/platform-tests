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

from ..constants import TapComponent
from ..tap_object_model import Application
from ..http_client.http_client_credentials import HttpClientCredentials
from ..http_client.http_client_type import HttpClientType


class UaaCredentialsProvider(object):
    """ Provide credentials for UAA http client. """

    _credentials = None

    @classmethod
    def get(cls) -> HttpClientCredentials:
        """ Return http credentials. """
        if cls._credentials is None:
            cls._provide_credentials()
        return cls._credentials

    @classmethod
    def _provide_credentials(cls):
        """ Retrieve credentials from user-management environment variables. """
        apps = Application.cf_api_get_list()
        user_management = next(a for a in apps if a.name == TapComponent.user_management.value)
        user_management_env = user_management.cf_api_env()
        upsi = user_management_env["VCAP_SERVICES"]["user-provided"]
        sso = next(x for x in upsi if x["name"] == "sso")
        cls._credentials = HttpClientCredentials(
            HttpClientType.UAA,
            sso["credentials"]["clientId"],
            sso["credentials"]["clientSecret"]
        )
