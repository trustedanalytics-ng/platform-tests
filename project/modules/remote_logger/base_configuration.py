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


class BaseConfiguration(object):
    """Base configuration object."""

    def __init__(self, from_date, to_date):
        self._validate("from_date", int, from_date)
        self._validate("to_date", int, to_date)
        self.__from_date = from_date
        self.__to_date = to_date

    @property
    def from_date(self):
        """Date in seconds format from which logs starts."""
        return self.__from_date

    @property
    def to_date(self):
        """Date in seconds format to which logs ends."""
        return self.__to_date

    @staticmethod
    def _validate(property_name, property_type, property_value):
        """Validate if given property has valid type and value."""
        if not property_value:
            raise ConfigurationEmptyPropertyException(property_name)
        if not isinstance(property_value, property_type):
            raise ConfigurationInvalidPropertyTypeException(property_name)


class ConfigurationEmptyPropertyException(Exception):
    TEMPLATE = "Property '{}' can not be empty."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))


class ConfigurationInvalidPropertyTypeException(Exception):
    TEMPLATE = "Property '{}' has invalid type."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
