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

import time

from requests.auth import AuthBase

from .client_auth_base import ClientAuthBase
from .http_method import HttpMethod
from .http_session import HttpSession
from .http_token_auth import HTTPTokenAuth


class ClientAuthToken(ClientAuthBase):
    """Base class that all token based http client authentication implementations derive from."""
    request_headers = {"Accept": "application/json"}
    token_life_time = 298
    token_name = "access_token"
    token_format = "Bearer {}"

    def __init__(self, url: str, session: HttpSession):
        self._token = None
        self._token_timestamp = None
        self._response = None
        super().__init__(url, session)

    @property
    def authenticated(self) -> bool:
        """Check if current user is authenticated."""
        return self._token and not self._is_token_expired()

    def authenticate(self) -> AuthBase:
        """Use session credentials to authenticate."""
        self._response = self.session.request(
            HttpMethod.POST, self._url,
            headers=self.request_headers,
            data=self.request_data,
            auth=("cf", ""),
            log_message="Retrieve token."
        )
        self._set_token()
        self._http_auth = HTTPTokenAuth(self._token)
        return self._http_auth

    def _is_token_expired(self):
        """Check if token has been expired."""
        return time.time() - self._token_timestamp > self.token_life_time

    def _set_token(self):
        """Set token taken from token request response."""
        if self.token_name not in self._response:
            raise ClientAuthTokenMissingResponseTokenKeyException()
        self._token_timestamp = time.time()
        self._token = self.token_format.format(self._response[self.token_name])

    @property
    def request_data(self) -> dict:
        """Token request data."""
        return {
            "username": self.session.username,
            "password": self.session.password,
            "grant_type": "password",
        }


class ClientAuthTokenMissingResponseTokenKeyException(Exception):
    def __init__(self):
        super().__init__("Token key is missing in token request response.")
