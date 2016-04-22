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

from datetime import datetime

from .config import Config

from .simulation.simulation_name import SimulationName


class GatlingRunnerParameters(object):
    """Gatling runner - run parameters."""

    def __init__(self, simulation_name: SimulationName, platform=None, organization=None, space=None, username=None,
                 password=None, proxy=None, proxy_http_port=None, proxy_https_port=None, users=None, users_at_once=None,
                 ramp=None, duration=None, repeat=None):
        self._validate("simulation", SimulationName, simulation_name)
        self._validate("platform", str, platform)
        self._validate("organization", str, organization)
        self._validate("space", str, space)
        self._validate("username", str, username)
        self._validate("password", str, password)
        self.__simulation_name = simulation_name
        self.__platform = platform
        self.__organization = organization
        self.__space = space
        self.__username = username
        self.__password = password
        self.__proxy = proxy
        self.__proxy_http_port = proxy_http_port
        self.__proxy_https_port = proxy_https_port
        self.__users = users
        self.__users_at_once = users_at_once
        self.__ramp = ramp
        self.__duration = duration
        self.__repeat = repeat
        self.__execution_directory = None
        self.__time = datetime.now().strftime("%s")

    @property
    def simulation_name(self):
        """Name of simulation class to run."""
        return self.__simulation_name

    @property
    def platform(self):
        """Tests platform domain."""
        return self.__platform

    @property
    def organization(self):
        """Platform organization name."""
        return self.__organization

    @property
    def space(self):
        """Platform organization space name."""
        return self.__space

    @property
    def username(self):
        """Platform username."""
        return self.__username

    @property
    def password(self):
        """Platform password."""
        return self.__password

    @property
    def proxy(self):
        """Connection proxy host name."""
        return self.__proxy if self.__proxy is not None else Config.GATLING_PROXY

    @property
    def proxy_http_port(self):
        """Connection proxy http port number."""
        return self.__proxy_http_port if self.__proxy_http_port is not None else Config.GATLING_PROXY_HTTP_PORT

    @property
    def proxy_https_port(self):
        """Connection proxy https port number."""
        return self.__proxy_https_port if self.__proxy_https_port is not None else Config.GATLING_PROXY_HTTPS_PORT

    @property
    def users(self):
        """Number of users for simulation to run."""
        return self.__users

    @property
    def users_at_once(self):
        """Number of users for simulation to run at once."""
        return self.__users_at_once

    @property
    def ramp(self):
        """Splitting users indicator. For example: users=10 and ramp=30.
        It basically means that our "users" will start interacting with our application progressively.
        In this case, after 3 seconds a new user will start doing our flow."""
        return self.__ramp

    @property
    def duration(self):
        """How many seconds to repeat simulation."""
        return self.__duration

    @property
    def repeat(self):
        """How many times to repeat simulation."""
        return self.__repeat

    @property
    def execution_directory(self):
        """Simulation execution directory."""
        return self.__execution_directory

    @execution_directory.setter
    def execution_directory(self, value):
        """Simulation execution directory setter."""
        self._validate("execution_directory", str, value)
        self.__execution_directory = value

    @property
    def log_file(self):
        """Execution log file."""
        return '{}_{}.log'.format(self.simulation_name.value, self.__time)

    @staticmethod
    def _validate(property_name, property_type, property_value):
        """Validate if given property has valid type and value."""
        if not property_value:
            raise GatlingRunnerParametersEmptyPropertyException(property_name)
        if not isinstance(property_value, property_type):
            raise GatlingRunnerParametersInvalidPropertyTypeException(property_name)


class GatlingRunnerParametersEmptyPropertyException(Exception):
    def __init__(self, message=None):
        super().__init__("Property '{}' can not be empty.".format(message))


class GatlingRunnerParametersInvalidPropertyTypeException(Exception):
    def __init__(self, message=None):
        super().__init__("Property '{}' has invalid type.".format(message))
