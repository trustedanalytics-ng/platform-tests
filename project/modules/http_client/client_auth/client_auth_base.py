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

from abc import ABCMeta, abstractmethod, abstractproperty

from requests.auth import AuthBase

from .http_session import HttpSession


class ClientAuthBase(object, metaclass=ABCMeta):
    """Base class that all http client authentication implementations derive from."""

    def __init__(self, url: str, session: HttpSession):
        self._url = url
        self.session = session
        self._http_auth = self.authenticate()

    @property
    def http_auth(self) -> AuthBase:
        """Http authentication method."""
        return self._http_auth

    @abstractproperty
    def authenticated(self) -> bool:
        """Is current user already authenticated."""

    @abstractmethod
    def authenticate(self) -> AuthBase:
        """Use session credentials to authenticate."""
