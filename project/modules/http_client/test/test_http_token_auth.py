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

from requests import Request

from ..client_auth.http_token_auth import HTTPTokenAuth


class TestHttpTokenAuth(unittest.TestCase):
    """Unit: HttpTokenAuth."""

    TOKEN = "11-22-33-44"

    def setUp(self):
        self._create_http_token_auth()
        super().setUp()

    def test_init(self):
        self.assertEqual(self.http_token_auth._token, self.TOKEN)

    def test_call(self):
        # given
        expected_headers = {"Authorization": self.TOKEN}
        # when
        auth_request = self.http_token_auth(Request())
        # then
        self.assertEqual(expected_headers, auth_request.headers, "Invalid request headers.")

    def _create_http_token_auth(self):
        self.http_token_auth = HTTPTokenAuth(self.TOKEN)


if __name__ == '__main__':
    unittest.main()
