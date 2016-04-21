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

from modules.http_client.http_client_credentials import HttpClientCredentials, \
    HttpClientCredentialsInvalidPropertyTypeException, HttpClientCredentialsEmptyPropertyException
from modules.http_client.http_client_type import HttpClientType


class TestHttpClientCredentials(unittest.TestCase):
    """Unit: HttpClientCredentials."""

    CLIENT_TYPE = HttpClientType.UAA
    USERNAME = "username"
    PASSWORD = "password"

    def test_init_should_return_valid_object_instance(self):
        credentials = HttpClientCredentials(self.CLIENT_TYPE, self.USERNAME, self.PASSWORD)
        self.assertEqual(self.CLIENT_TYPE, credentials.client_type)
        self.assertEqual(self.USERNAME, credentials.username)
        self.assertEqual(self.PASSWORD, credentials.password)
        self.assertEqual("HttpClientType.UAA_username_password", credentials.uid)
        self.assertIsInstance(credentials, HttpClientCredentials, "Invalid credentials class.")

    def test_init_should_return_exception_when_invalid_property_type(self):
        self.assertRaises(
            HttpClientCredentialsInvalidPropertyTypeException,
            HttpClientCredentials,
            "Undefined",
            self.USERNAME,
            self.PASSWORD,
        )

    def test_init_should_return_exception_when_empty_property_value(self):
        self.assertRaises(
            HttpClientCredentialsEmptyPropertyException,
            HttpClientCredentials,
            "",
            self.USERNAME,
            self.PASSWORD,
        )


if __name__ == '__main__':
    unittest.main()
