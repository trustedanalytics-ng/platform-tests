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
import json
import os


class _BaseConfig(object):
    _default_config = {}

    def __init__(self):
        self._config = self._default_config.copy()
        self._config.update(self._parse_environment_variables())

    @abc.abstractmethod
    def _parse_environment_variables(self) -> dict:
        pass

    def __getattr__(self, item):
        return self._config.get(item)


class DatabaseConfig(_BaseConfig):
    """
    example environment variable setting:
        VCAP_SERVICES={
            "mongodb26": [{
                "credentials": {
                    "dbname": <db_name>,
                    "hostname": <db_host_name>,
                    "password": <user_password>,
                    "username": <user_name>,
                    "port": <db_connection_port_number>,
                    "uri": "mongodb://username:password@hostname:port/dbname"
                }
            }]
        }
    """
    VCAP_SERVICES = "VCAP_SERVICES"
    _default_config = {
        "uri": "mongodb://localhost:27017/test_results",
        "dbname": "test_results",
        "hostname": "localhost",
        "port": 27017,
        "test_suite_collection": "test_run",
        "test_result_collection": "test_result",
    }

    def _parse_environment_variables(self) -> dict:
        environment_config = os.environ.get(self.VCAP_SERVICES, {})
        if environment_config != {}:
            environment_config = json.loads(environment_config)
            environment_config = environment_config["mongodb26"][0]["credentials"]
            environment_config["port"] = int(environment_config["port"])
        return environment_config


class AppConfig(_BaseConfig):
    """
    example environment variable setting:
        VCAP_APP_PORT=8080
    """
    VCAP_APP_PORT = "VCAP_APP_PORT"
    _default_config = {
        "hostname": "0.0.0.0",
        "port": 8080,
        "debug": False,
    }

    def _parse_environment_variables(self) -> dict:
        environment_config = {}
        vcap_app_port = os.environ.get(self.VCAP_APP_PORT)
        if vcap_app_port is not None:
            environment_config["port"] = int(vcap_app_port)
        return environment_config


class RunnerConfig(_BaseConfig):
    """
    example environment variable setting:
    required:
        VCAP_APPLICATION={"uris": ["platform-tests.<tapdomain>"]}
        REFERENCE_ORG=<reference_org_name>
        REFERENCE_SPACE=<reference_space_name>
    use only locally:
        INTERPRETER=<path to interpreter to use with run_tests.py>
    """
    VCAP_APPLICATION = "VCAP_APPLICATION"
    REFERENCE_ORG = "REFERENCE_ORG"
    REFERENCE_SPACE = "REFERENCE_SPACE"
    _default_config = {
        "reference_org": "seedorg",
        "reference_space": "seedspace",
        "python_interpreter": "python3",
        "run_tests": "run_tests.py",
        "cwd": "project",
        "suite_name": "test_smoke/test_functional.py",
        "max_execution_time": 1800,  # 30 minutes
    }

    def _parse_environment_variables(self) -> dict:
        environment_config = {}

        try:
            vcap_application = json.loads(os.environ[self.VCAP_APPLICATION])
            environment_config["tap_domain"] = vcap_application["uris"][0].split(".", 1)[1]
        except KeyError:
            raise IncorrectConfigurationException()

        reference_org = os.environ.get(self.REFERENCE_ORG)
        if reference_org is not None:
            environment_config["reference_org"] = reference_org
        reference_space = os.environ.get(self.REFERENCE_SPACE)
        if reference_space is not None:
            environment_config["reference_space"] = reference_space

        return environment_config


class IncorrectConfigurationException(Exception):

    def __init__(self):
        super().__init__("Environment variables not set properly")
