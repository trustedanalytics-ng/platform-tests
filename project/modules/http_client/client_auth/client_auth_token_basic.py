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

from .client_auth_token_base import ClientAuthTokenBase


# noinspection PyAbstractClass
class ClientAuthTokenBasic(ClientAuthTokenBase):
    """Basic token based http client authentication."""

    @property
    def request_headers(self) -> dict:
        """Token request headers."""
        return {
            "Accept": "application/json"
        }

    @property
    def request_data(self) -> dict:
        """Token request data."""
        return {
            "username": self.session.username,
            "password": self.session.password,
            "grant_type": "password"
        }

    @property
    def token_format(self) -> str:
        """Token format."""
        return "Bearer {}"

    @property
    def token_life_time(self) -> int:
        """Token life time in seconds."""
        return 298

    @property
    def token_name(self) -> str:
        """Token name."""
        return "access_token"
