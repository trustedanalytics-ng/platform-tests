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

from ..config import Config
from .http_session import HttpSession
from .client_auth_base import ClientAuthBase
from .client_auth_http_basic import ClientAuthHttpBasic
from .client_auth_login_page import ClientAuthLoginPage
from .client_auth_token import ClientAuthToken
from .client_auth_type import ClientAuthType


class ClientAuthFactory(object):
    """Client authentication factory."""

    @staticmethod
    def get(username: str, password: str, auth_type: ClientAuthType) -> ClientAuthBase:
        """Create client authentication for given type."""
        session = HttpSession(username, password)

        if auth_type == ClientAuthType.TOKEN_CF:
            return ClientAuthToken(Config.auth_basic_token_url(), session)

        if auth_type == ClientAuthType.TOKEN_UAA:
            return ClientAuthToken(Config.auth_uaa_token_url(), session)

        elif auth_type == ClientAuthType.HTTP_BASIC:
            return ClientAuthHttpBasic("", session)

        elif auth_type == ClientAuthType.LOGIN_PAGE:
            return ClientAuthLoginPage(Config.auth_login_url(), session)

        else:
            raise ClientAuthFactoryInvalidAuthTypeException(auth_type)


class ClientAuthFactoryInvalidAuthTypeException(Exception):
    TEMPLATE = "Client authentication with type {} is not implemented."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
