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

from modules.http_client.unittests.mock_http_session import MockHttpSession
from modules.http_client.client_auth.client_auth_token_basic import ClientAuthTokenBasic
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.client_auth.http_session import HttpSession
from modules.http_client.http_client import HttpClient


class TestHttpClient(MockHttpSession):
    """Unit: HttpClient."""

    URL = "http://some.url"

    def setUp(self):
        self.mock_http_session()
        self._create_http_client()
        super().setUp()

    def test_init(self):
        self.assertEqual(self.URL, self.http_client.url)
        self.assertIsInstance(self.http_client._auth, ClientAuthTokenBasic, "Invalid auth class.")

    def test_request(self):
        response = self.http_client.request(HttpMethod.GET, "/some/path")
        self.assertEqual(response, self.http_session_response)

    def _create_http_client(self):
        self.http_client = HttpClient(
            self.URL,
            ClientAuthTokenBasic(
                "http://auth.url",
                HttpSession(
                    "username",
                    "password"
                )
            )
        )


if __name__ == '__main__':
    unittest.main()
