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
    """
    example environment variable setting:
    required:
        VCAP_APPLICATION={"uris": ["platform-tests.<tapdomain>"]}
    """
    _default_config = {}
    VCAP_APPLICATION = "VCAP_APPLICATION"

    def __init__(self):
        self._config = self._default_config.copy()
        self._config.update(self._parse_environment_variables())

    @abc.abstractmethod
    def _parse_environment_variables(self) -> dict:
        pass

    def _parse_tap_domain(self):
        try:
            vcap_application = json.loads(os.environ[self.VCAP_APPLICATION])
            return vcap_application["uris"][0].split(".", 1)[1]
        except KeyError:
            raise IncorrectConfigurationException()

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
        environment_config["tap_domain"] = self._parse_tap_domain()
        vcap_app_port = os.environ.get(self.VCAP_APP_PORT)
        if vcap_app_port is not None:
            environment_config["port"] = int(vcap_app_port)
        return environment_config


class RunnerConfig(_BaseConfig):
    """
    example environment variable setting:
    required:
        CORE_ORG_NAME=<core_org_name>
        CORE_SPACE_NAME=<core_space_name>
    use only locally:
        LOCAL_INTERPRETER=<path to interpreter to use with run_tests.py>
    """
    CORE_ORG_NAME = "CORE_ORG_NAME"
    CORE_SPACE_NAME = "CORE_SPACE_NAME"
    LOCAL_INTERPRETER = "LOCAL_INTERPRETER"
    _default_config = {
        "core_org_name": "trustedanalytics",
        "core_space_name": "platform",
        "python_interpreter": "python3",
        "run_tests": "run_tests.py",
        "cwd": "project",
        "suite_name": "test_smoke/test_functional.py",
        "max_execution_time": 1800,  # 30 minutes
    }

    def _parse_environment_variables(self) -> dict:
        environment_config = {}
        environment_config["tap_domain"] = self._parse_tap_domain()
        core_org_name = os.environ.get(self.CORE_ORG_NAME)
        if core_org_name is not None:
            environment_config["core_org_name"] = core_org_name
        core_space_name = os.environ.get(self.CORE_SPACE_NAME)
        if core_space_name is not None:
            environment_config["core_space_name"] = core_space_name
        local_interpreter = os.environ.get(self.LOCAL_INTERPRETER)
        if local_interpreter is not None:
            environment_config["python_interpreter"] = os.path.expanduser(local_interpreter)

        return environment_config


class IncorrectConfigurationException(Exception):

    def __init__(self):
        super().__init__("Environment variables not set properly")
