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

import abc
import os
import sys


class Paths:

    PLATFORM_TESTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    PROJECT_DIR = os.path.join(PLATFORM_TESTS_DIR, "project")


class _BaseConfig(object):
    """
    example environment variable setting:
    required:
        PT_TAP_DOMAIN=environment_address
    """
    _default_config = {}
    PT_TAP_DOMAIN = "PT_TAP_DOMAIN"

    def __init__(self):
        self._config = self._default_config.copy()
        self._config.update(self._parse_environment_variables())

    @abc.abstractmethod
    def _parse_environment_variables(self) -> dict:
        pass

    def _parse_tap_domain(self):
        tap_domain = os.environ.get(self.PT_TAP_DOMAIN)
        if not tap_domain:
            raise IncorrectConfigurationException("Missing env {}".format(self.PT_TAP_DOMAIN))
        return tap_domain

    def __getattr__(self, item):
        return self._config.get(item)


class DatabaseConfig(_BaseConfig):
    """
    example environment variable setting:
        MONGODB_HOST=localhost
        MONGODB_PORT=27017
    """
    MONGODB_HOST = "MONGODB_HOST"
    MONGODB_PORT = "MONGODB_PORT"
    MONGODB_DBNAME = "MONGODB_DBNAME"
    MONGODB_USERNAME = "MONGODB_USERNAME"
    MONGODB_PASSWORD = "MONGODB_PASSWORD"
    _default_config = {
        "dbname": "test_results",
        "hostname": "localhost",
        "port": 27017,
        "test_suite_collection": "test_run",
        "test_result_collection": "test_result",
        "username": None,
        "password": None
    }

    @property
    def uri(self):
        credentials = ""
        if self._are_credentials_present():
            credentials = "{}:{}@".format(self.username, self.password)
        return "mongodb://{}{}:{}/{}".format(credentials, self.hostname, self.port, self.dbname)

    def _parse_environment_variables(self) -> dict:
        environment_config = {}

        hostname = os.environ.get(self.MONGODB_HOST)
        if hostname:
            environment_config['hostname'] = hostname

        port = os.environ.get(self.MONGODB_PORT)
        if port:
            environment_config['port'] = int(port)

        dbname = os.environ.get(self.MONGODB_DBNAME)
        if dbname:
            environment_config['dbname'] = dbname

        username = os.environ.get(self.MONGODB_USERNAME)
        if username:
            environment_config['username'] = username

        password = os.environ.get(self.MONGODB_PASSWORD)
        if password:
            environment_config['password'] = password

        return environment_config

    def _are_credentials_present(self) -> bool:
        if None not in [self.username, self.password]:
            return True
        return False


class AppConfig(_BaseConfig):
    """
    example environment variable setting:
        PORT=80
    """
    PORT = "PORT"
    DEBUG = "DEBUG"
    PROTOCOL = "ACCESS_PROTOCOL"
    _default_config = {
        "hostname": "0.0.0.0",
        "port": 8080,
        "debug": False,
        "protocol": "http"
    }

    def _parse_environment_variables(self) -> dict:
        environment_config = {"tap_domain": self._parse_tap_domain()}
        port = os.environ.get(self.PORT)
        if port:
            environment_config["port"] = int(port)
        debug = os.environ.get(self.DEBUG)
        if debug and debug in ["1", "True", "true"]:
            environment_config["port"] = True
        access_protocol = os.environ.get(self.PROTOCOL)
        if access_protocol == "https":
            environment_config["protocol"] = access_protocol
        return environment_config


class RunnerConfig(_BaseConfig):

    _default_config = {
        "pytest_command": [sys.executable, "-m", "pytest"],
        "cwd": Paths.PROJECT_DIR,
        "suite_path": os.path.join(Paths.PROJECT_DIR, "tests/test_smoke/test_functional.py"),
        "max_execution_time": 1800,  # 30 minutes
    }

    def _parse_environment_variables(self) -> dict:
        return {"tap_domain": self._parse_tap_domain()}


class IncorrectConfigurationException(Exception):

    def __init__(self, msg="Environment variables not set properly"):
        super().__init__(msg)
