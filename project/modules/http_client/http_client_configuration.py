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

from .http_client_type import HttpClientType


class HttpClientConfiguration(object):
    """Http client configuration."""

    def __init__(self, client_type: HttpClientType, url: str, username: str, password: str):
        self._validate("client_type", HttpClientType, client_type)
        self._validate("url", str, url)
        self._validate("username", str, username)
        self._client_type = client_type
        self._url = url
        self._username = username
        self._password = password

    @property
    def client_type(self):
        """Client type."""
        return self._client_type

    @property
    def url(self):
        """Client api url address."""
        return self._url

    @property
    def username(self):
        """Client auth username."""
        return self._username

    @property
    def password(self):
        """Client auth password."""
        return self._password

    @property
    def uid(self):
        """Client configuration unique id."""
        return "{}_{}_{}_{}".format(self.client_type, self.url, self.username, self.password)

    @staticmethod
    def _validate(property_name, property_type, property_value):
        """Validate if given property has valid type and value."""
        if not property_value:
            raise HttpClientConfigurationEmptyPropertyException(property_name)
        if not isinstance(property_value, property_type):
            raise HttpClientConfigurationInvalidPropertyTypeException(property_name)


class HttpClientConfigurationEmptyPropertyException(Exception):
    TEMPLATE = "Property '{}' can not be empty."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))


class HttpClientConfigurationInvalidPropertyTypeException(Exception):
    TEMPLATE = "Property '{}' has invalid type."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
