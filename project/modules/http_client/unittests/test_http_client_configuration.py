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

from modules.http_client.http_client_type import HttpClientType
from modules.http_client.http_client_configuration import HttpClientConfiguration, \
    HttpClientConfigurationInvalidPropertyTypeException, HttpClientConfigurationEmptyPropertyException


class TestHttpClientConfiguration(unittest.TestCase):
    """Unit: HttpClientConfiguration."""

    CLIENT_TYPE = HttpClientType.UAA
    URL = "api.test.platform.eu"
    USERNAME = "username"
    PASSWORD = "password"

    def test_init_should_return_valid_object_instance(self):
        configuration = HttpClientConfiguration(self.CLIENT_TYPE, self.URL, self.USERNAME, self.PASSWORD)
        self.assertEqual(self.CLIENT_TYPE, configuration.client_type)
        self.assertEqual(self.URL, configuration.url)
        self.assertEqual(self.USERNAME, configuration.username)
        self.assertEqual(self.PASSWORD, configuration.password)
        self.assertEqual("HttpClientType.UAA_username_password", configuration.uid)
        self.assertIsInstance(configuration, HttpClientConfiguration, "Invalid credentials class.")

    def test_init_should_return_exception_when_invalid_property_type(self):
        self.assertRaises(
            HttpClientConfigurationInvalidPropertyTypeException,
            HttpClientConfiguration,
            "Undefined",
            self.URL,
            self.USERNAME,
            self.PASSWORD,
        )

    def test_init_should_return_exception_when_empty_property_value(self):
        self.assertRaises(
            HttpClientConfigurationEmptyPropertyException,
            HttpClientConfiguration,
            "",
            self.URL,
            self.USERNAME,
            self.PASSWORD,
        )


if __name__ == '__main__':
    unittest.main()
