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
from modules.http_client.client_auth.client_auth_no_auth import ClientAuthNoAuth
from modules.http_client.unittests.mock_http_session import MockHttpSession
from modules.http_client.client_auth.client_auth_base import ClientAuthBase
from modules.http_client.client_auth.client_auth_token import ClientAuthToken
from modules.http_client.http_client import HttpClient
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.http_client_type import HttpClientType


class TestHttpClientFactory(MockHttpSession):
    """Unit: HttpClientFactory."""

    USERNAME = "username"
    PASSWORD = "password"

    def setUp(self):
        HttpClientFactory._INSTANCES = {}
        self.mock_http_session()
        super().setUp()

    def test_get_should_return_client_for_uaa(self):
        self._assertHttpClientInstance(HttpClientType.UAA, ClientAuthToken)

    def test_get_should_return_client_for_cf(self):
        self._assertHttpClientInstance(HttpClientType.CLOUD_FOUNDRY, ClientAuthToken)

    def test_get_should_return_client_for_application(self):
        self._assertHttpClientInstance(HttpClientType.APPLICATION, ClientAuthToken)

    def test_get_should_return_client_for_application_broker(self):
        self._assertHttpClientInstance(HttpClientType.BROKER, ClientAuthHttpBasic)

    def test_get_should_return_client_for_service_tool(self):
        self._assertHttpClientInstance(HttpClientType.SERVICE_TOOL, ClientAuthNoAuth)

    def test_get_should_create_only_one_instance(self):
        # given
        configuration = self._get_configuration(HttpClientType.APPLICATION)
        self.assertNotIn(configuration.uid, HttpClientFactory._INSTANCES, "Invalid instance reference.")
        # when
        HttpClientFactory.get(configuration)
        HttpClientFactory.get(configuration)
        # then
        self.assertIn(configuration.uid, HttpClientFactory._INSTANCES, "Missing instance reference.")
        self.assertEqual(1, len(HttpClientFactory._INSTANCES), "Invalid number of instances.")

    def test_get_should_return_new_instance_after_remove(self):
        # given
        configuration = self._get_configuration(HttpClientType.BROKER)
        self.assertNotIn(configuration.uid, HttpClientFactory._INSTANCES, "Invalid instance reference.")
        client = HttpClientFactory.get(configuration)
        self.assertEqual(client._auth.session.username, self.USERNAME)
        self.assertEqual(client._auth.session.password, self.PASSWORD)
        # when
        HttpClientFactory.remove(configuration)
        new_configuration = self._get_configuration(HttpClientType.BROKER, self.USERNAME, "new_password")
        new_client = HttpClientFactory.get(new_configuration)
        # then
        self.assertNotIn(configuration.uid, HttpClientFactory._INSTANCES)
        self.assertIn(new_configuration.uid, HttpClientFactory._INSTANCES)
        self.assertEqual(1, len(HttpClientFactory._INSTANCES), "Invalid number of instances.")
        self.assertEqual(new_client._auth.session.username, self.USERNAME)
        self.assertEqual(new_client._auth.session.password, "new_password")

    def _assertHttpClientInstance(self, client_type, auth: ClientAuthBase):
        configuration = self._get_configuration(client_type)
        client = HttpClientFactory.get(configuration)
        self.assertIsInstance(client, HttpClient, "Invalid client class.")
        self.assertIsInstance(client._auth, auth, "Invalid auth class.")
        self.assertIn(configuration.uid, HttpClientFactory._INSTANCES, "Missing instance reference.")

    def _get_configuration(self, client_type, username=USERNAME, password=PASSWORD):
        return HttpClientConfiguration(client_type, "api.test.platform.eu", username, password)


if __name__ == '__main__':
    unittest.main()
