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
import logging


# environment variables to set
VCAP_SERVICES = "VCAP_SERVICES"
LOG_LEVEL = "LOG_LEVEL"
VCAP_APP_PORT = "VCAP_APP_PORT"

logger = logging.getLogger(__name__)


class NoConfigurationError(Exception):
    pass


class Config(object):

    def __init__(self):
        """
        Reads configuration from environment variables, also those set by Cloud Foundry.
        If the application is run locally, export VCAP_SERVICES with the following value:
        {
            "mongodb26": [
                {
                    "credentials": {
                     "dbname": <db_name>,
                     "hostname": <db_host_name>,
                     "password": <user_password>,
                     "username": <user_name>,
                     "port": <db_connection_port_number>
                }
            ]
        }
        """

        try:
            vcap_services = os.environ[VCAP_SERVICES]
        except KeyError:
            raise NoConfigurationError("VCAP_SERVICES environment variable not set")

        mongodb_credentials = json.loads(vcap_services)["mongodb26"][0]["credentials"]
        self.db_name = mongodb_credentials.get("dbname")
        self.db_username = mongodb_credentials.get("username")
        self.db_password = mongodb_credentials.get("password")
        self.db_hostname = mongodb_credentials.get("hostname", "localhost")
        self.db_port = int(mongodb_credentials.get("port", "27017"))
        self.log_level = os.environ.get(LOG_LEVEL, "DEBUG")
        self.app_port = int(os.environ.get(VCAP_APP_PORT, "5000"))
        self.app_host = "0.0.0.0"
        logger.info("DB name: {}, DB username: {}, DB password: {}, DB hostname: {}, DB port: {}"
                    .format(self.db_name, self.db_username, self.db_password, self.db_hostname, self.db_port))

