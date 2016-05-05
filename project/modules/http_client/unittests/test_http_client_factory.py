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

import unittest
from modules.http_client.client_auth.client_auth_http_basic import ClientAuthHttpBasic

from modules.http_client.unittests.mock_http_session import MockHttpSession
from modules.http_client.client_auth.client_auth_base import ClientAuthBase
from modules.http_client.client_auth.client_auth_token_uaa import ClientAuthTokenUaa
from modules.http_client.client_auth.client_auth_token_basic import ClientAuthTokenBasic
from modules.http_client.http_client import HttpClient
from modules.http_client.http_client_credentials import HttpClientCredentials
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.http_client_type import HttpClientType


class TestHttpClientFactory(MockHttpSession):
    """Unit: HttpClientFactory."""

    def setUp(self):
        self.mock_http_session()
        super().setUp()

    def test_get_should_return_client_for_uaa(self):
        self._assertHttpClientInstance(HttpClientType.UAA, ClientAuthTokenUaa)

    def test_get_should_return_client_for_cf(self):
        self._assertHttpClientInstance(HttpClientType.CLOUD_FOUNDRY, ClientAuthTokenBasic)

    def test_get_should_return_client_for_platform(self):
        self._assertHttpClientInstance(HttpClientType.PLATFORM, ClientAuthTokenBasic)

    def test_get_should_return_client_for_application_broker(self):
        self._assertHttpClientInstance(HttpClientType.APPLICATION_BROKER, ClientAuthHttpBasic)

    def test_get_should_return_client_for_console(self):
        credentials = self._get_credentials(HttpClientType.CONSOLE)
        self.assertRaises(NotImplementedError, HttpClientFactory.get, credentials)

    def test_get_should_create_only_one_instance(self):
        # given
        credentials = HttpClientCredentials(HttpClientType.UAA, "username", "password")
        self.assertNotIn(credentials.uid, HttpClientFactory._INSTANCES, "Invalid instance reference.")
        # when
        HttpClientFactory.get(credentials)
        HttpClientFactory.get(credentials)
        # then
        self.assertIn(credentials.uid, HttpClientFactory._INSTANCES, "Missing instance reference.")
        self.assertEqual(1, len(HttpClientFactory._INSTANCES), "Invalid number of instances.")

    def _assertHttpClientInstance(self, client_type, auth: ClientAuthBase):
        credentials = self._get_credentials(client_type)
        client = HttpClientFactory.get(credentials)
        self.assertIsInstance(client, HttpClient, "Invalid client class.")
        self.assertIsInstance(client._auth, auth, "Invalid auth class.")
        self.assertIn(credentials.uid, HttpClientFactory._INSTANCES, "Missing instance reference.")

    def _get_credentials(self, client_type):
        return HttpClientCredentials(client_type, "username", "password")


if __name__ == '__main__':
    unittest.main()
