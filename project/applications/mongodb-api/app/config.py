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


class MongoLabel:
    MONGODB26 = "mongodb26"
    MONGODB30_MULTINODE = "mongodb30-multinode"


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
            self.mongodb_version = list(json.loads(vcap_services).keys())[0]
        except KeyError:
            raise NoConfigurationError("VCAP_SERVICES environment variable not set")

        mongodb_credentials = json.loads(vcap_services)[self.mongodb_version][0]["credentials"]
        self.db_name = mongodb_credentials.get("dbname")
        self.db_username = mongodb_credentials.get("username")
        self.db_password = mongodb_credentials.get("password")
        if self.mongodb_version == MongoLabel.MONGODB26:
            self.db_hostname0 = mongodb_credentials.get("hostname", "localhost")
            self.db_port0 = int(mongodb_credentials.get("port", "27017"))
        elif self.mongodb_version == MongoLabel.MONGODB30_MULTINODE:
            self.db_hostname0 = mongodb_credentials["replicas"][0]["host"]
            self.db_port0 = int(mongodb_credentials["replicas"][0]["ports"]["27017/tcp"])
            self.db_hostname1 = mongodb_credentials["replicas"][1]["host"]
            self.db_port1 = int(mongodb_credentials["replicas"][1]["ports"]["27017/tcp"])
            self.db_hostname2 = mongodb_credentials["replicas"][2]["host"]
            self.db_port2 = int(mongodb_credentials["replicas"][2]["ports"]["27017/tcp"])
        else:
            raise Exception("Unexpected MongoDB label")
        self.log_level = os.environ.get(LOG_LEVEL, "DEBUG")
        self.app_port = int(os.environ.get(VCAP_APP_PORT, "5000"))
        self.app_host = "0.0.0.0"
        logger.info("DB name: {}, DB username: {}, DB password: {}, DB hostname: {}, DB port: {}"
                    .format(self.db_name, self.db_username, self.db_password, self.db_hostname0, self.db_port0))

