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

import sys

import config
from .http_session import HttpSession
from .client_auth_base import ClientAuthBase
from .client_auth_http_basic import ClientAuthHttpBasic
from .client_auth_login_page import ClientAuthLoginPage
from .client_auth_token import ClientAuthToken
from .k8s_client_auth_token import K8sClientAuthToken
from .client_auth_type import ClientAuthType
from .client_auth_no_auth import ClientAuthNoAuth
from .webhdfs_session import WebhdfsSession


class ClientAuthFactory(object):
    """Client authentication factory."""

    EMPTY_URL = ""

    @staticmethod
    def get(username: str, password: str, auth_type: ClientAuthType, proxies: dict=None) -> ClientAuthBase:
        """Create client authentication for given type."""
        session = HttpSession(username, password, proxies)

        if auth_type == ClientAuthType.TOKEN_CF:
            return ClientAuthToken(config.cf_oauth_token_url, session)

        elif auth_type == ClientAuthType.TOKEN_UAA:
            return ClientAuthToken(config.uaa_oauth_token_url, session)

        elif auth_type == ClientAuthType.HTTP_BASIC:
            return ClientAuthHttpBasic(ClientAuthFactory.EMPTY_URL, session)

        elif auth_type == ClientAuthType.TOKEN_K8S_AS:
            return K8sClientAuthToken(config.ng_k8s_as_oauth_token_url, session)

        elif auth_type == ClientAuthType.LOGIN_PAGE:
            return ClientAuthLoginPage(config.console_login_url, session)

        elif auth_type == ClientAuthType.WEBHDFS:
            return ClientAuthNoAuth(ClientAuthFactory.EMPTY_URL, WebhdfsSession(username, password))

        elif auth_type == ClientAuthType.NO_AUTH:
            return ClientAuthNoAuth(ClientAuthFactory.EMPTY_URL, session)

        else:
            raise ClientAuthFactoryInvalidAuthTypeException(auth_type)


class ClientAuthFactoryInvalidAuthTypeException(Exception):
    TEMPLATE = "Client authentication with type {} is not implemented."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
