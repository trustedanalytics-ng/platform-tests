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

import os
import json


class Config(object):
    """Main package configuration."""

    SERVICES = "VCAP_SERVICES"

    def __init__(self):
        """
        Reads configuration from environment variables, also those set by Cloud Foundry.
        If the application is run locally, export VCAP_SERVICES with the following value:
        {
            "orientdb": [
               {
                    "credentials": {
                        "hostname": "<host_name>",
                        "username": "<user_name>",
                        "password": "<password>",
                        "ports": {
                            "2424/tcp": "<port_number>",
                            "2480/tcp": "<port_number>"
                        }
                    }
                }
            ]
        }
        """
        credentials = self._get_credentials()
        self.db_username = credentials.get("username", "root")
        self.db_password = credentials.get("password")
        self.db_hostname = credentials.get("hostname", "localhost")
        ports = credentials.get("ports")
        self.db_port = int(ports["2424/tcp"])

    @classmethod
    def _get_credentials(cls):
        """Get credentials from environment."""
        try:
            services = os.environ[cls.SERVICES]
        except KeyError:
            raise MissingConfigurationError("Environment variable '{}' is missing.".format(cls.SERVICES))
        return json.loads(services)["orientdb"][0]["credentials"]


class MissingConfigurationError(Exception):
    pass
