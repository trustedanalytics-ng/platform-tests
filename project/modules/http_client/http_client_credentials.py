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


class HttpClientCredentials(object):
    """Http client credentials."""

    def __init__(self, client_type: HttpClientType, username: str, password: str):
        self._validate("client_type", HttpClientType, client_type)
        self._validate("username", str, username)
        self._validate("password", str, password)
        self._client_type = client_type
        self._username = username
        self._password = password

    @property
    def client_type(self):
        """Client type."""
        return self._client_type

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
        """Client credentials unique id."""
        return "{}_{}_{}".format(self.client_type, self.username, self.password)

    @staticmethod
    def _validate(property_name, property_type, property_value):
        """Validate if given property has valid type and value."""
        if not property_value:
            raise HttpClientCredentialsEmptyPropertyException(property_name)
        if not isinstance(property_value, property_type):
            raise HttpClientCredentialsInvalidPropertyTypeException(property_name)


class HttpClientCredentialsEmptyPropertyException(Exception):
    TEMPLATE = "Property '{}' can not be empty."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))


class HttpClientCredentialsInvalidPropertyTypeException(Exception):
    TEMPLATE = "Property '{}' has invalid type."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
