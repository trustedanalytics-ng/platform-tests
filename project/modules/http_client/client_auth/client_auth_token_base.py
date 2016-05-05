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
from abc import ABCMeta, abstractproperty

from requests.auth import AuthBase

from .client_auth_base import ClientAuthBase
from .http_method import HttpMethod
from .http_token_auth import HTTPTokenAuth
from .http_session import HttpSession


class ClientAuthTokenBase(ClientAuthBase, metaclass=ABCMeta):
    """Base class that all token based http client authentication implementations derive from."""

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
            log_message="Token has been retrieved."
        )
        self._set_token()
        return HTTPTokenAuth(self._token)

    def _is_token_expired(self):
        """Check if token has been expired."""
        return time.time() - self._token_timestamp > self.token_life_time

    def _set_token(self):
        """Set token taken from token request response."""
        if self.token_name not in self._response:
            raise ClientAuthTokenMissingResponseTokenKeyException()
        self._token_timestamp = time.time()
        self._token = self.token_format.format(self._response[self.token_name])

    @abstractproperty
    def request_data(self) -> dict:
        """Token request data."""

    @abstractproperty
    def request_headers(self) -> dict:
        """Token request headers."""

    @abstractproperty
    def token_life_time(self) -> int:
        """Token life time in seconds."""

    @abstractproperty
    def token_name(self) -> str:
        """Token name."""

    @abstractproperty
    def token_format(self) -> str:
        """Token format."""


class ClientAuthTokenMissingResponseTokenKeyException(Exception):
    def __init__(self):
        super().__init__("Token key is missing in token request response.")
