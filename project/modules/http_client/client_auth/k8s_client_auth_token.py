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

from requests.auth import AuthBase

import config
from .client_auth_token import ClientAuthToken
from .http_method import HttpMethod
from .http_token_auth import HTTPTokenAuth


class K8sClientAuthToken(ClientAuthToken):

    def authenticate(self) -> AuthBase:
        """Use session credentials to authenticate."""
        credentials = config.ng_k8s_service_credentials()
        self._response = self.session.request(
            HttpMethod.GET, self._url,
            headers=self.request_headers,
            auth=credentials,
            log_message="Retrieve token."
        )
        self._set_token()
        self._http_auth = HTTPTokenAuth(self._token_header)
        return self._http_auth
