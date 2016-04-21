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

from .base_configuration import BaseConfiguration


class RemoteLoggerConfiguration(BaseConfiguration):
    """Remote logger configuration object."""

    def __init__(self, from_date, to_date, app_names, destination_directory):
        super().__init__(from_date, to_date)
        self._validate("app_names", tuple, app_names)
        self._validate("destination_directory", str, destination_directory)
        self.__app_names = app_names
        self.__destination_directory = destination_directory

    @property
    def app_names(self):
        """List of application names."""
        return self.__app_names

    @property
    def destination_directory(self):
        """Directory to store log files."""
        return self.__destination_directory
