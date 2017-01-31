#
# Copyright (c) 2016-2017 Intel Corporation
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

import json
import unittest
from unittest.mock import patch

from requests import Session, Response

from modules.constants.http_status import HttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.client_auth.http_session import HttpSession


class TestHttpSession(unittest.TestCase):
    """Unit: HttpSession."""

    USERNAME = "username"
    PASSWORD = "password"
    PATH = "path"
    URL = "http://some"

    def setUp(self):
        self._create_http_session()
        super().setUp()

    def test_init(self):
        self.assertEqual(self.USERNAME, self.http_session.username)
        self.assertEqual(self.PASSWORD, self.http_session.password)
        self.assertIsInstance(self.http_session._session, Session, "Invalid session class.")

    @patch("requests.Session.send")
    def test_request_should_return_valid_response(self, mock_session_send_call):
        # given
        content = b'{"status":"ok"}'
        expected_response = json.loads(content.decode())
        response = Response()
        response.status_code = HttpStatus.CODE_OK
        response._content = content
        mock_session_send_call.return_value = response
        # when
        response = self.http_session.request(HttpMethod.GET, self.URL, self.PATH)
        # then
        self.assertEqual(response, expected_response)

    @patch("requests.Session.send")
    def test_request_should_return_valid_response(self, mock_session_send_call):
        # given
        response = Response()
        response.status_code = HttpStatus.CODE_BAD_REQUEST
        mock_session_send_call.return_value = response
        # then
        self.assertRaises(UnexpectedResponseError, self.http_session.request, HttpMethod.GET, self.URL, self.PATH)

    def _create_http_session(self):
        self.http_session = HttpSession(
            self.USERNAME,
            self.PASSWORD
        )


if __name__ == '__main__':
    unittest.main()
