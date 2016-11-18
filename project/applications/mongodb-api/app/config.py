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
import logging

from retry import retry

# environment variables to set
LOG_LEVEL = "LOG_LEVEL"
APP_PORT = "APP_PORT"

logging.basicConfig()
logger = logging.getLogger(__name__)


MongoVersion = {
    '26': 'mongodb26',
    '30': 'mongodb30',
    '30_MULTINODE': 'mongodb30_multinode',
}

MONGODB_SERVER_PORT = 27017


class Config(object):

    def __init__(self):
        """
        Reads configuration from environment variables.

        Raises:
            Raises KeyError when missing environment variable.
        """
        mongodb_credentials = self._load_database_credentials_and_type()

        try:
            self.db_type = mongodb_credentials['db_type'].encode('ascii', 'ignore')
            self.db_name = mongodb_credentials['db_name'].encode('ascii', 'ignore')
            self.db_username = mongodb_credentials['username'].encode('ascii', 'ignore')
            self.db_password = mongodb_credentials['password'].encode('ascii', 'ignore')
            self.db_hostname = mongodb_credentials['hostname'].encode('ascii', 'ignore')
            self.db_port = int(mongodb_credentials['port'])
        except KeyError as e:
            raise ConfigurationError("Missing {} in service credentials".format(e))

        self.log_level = os.environ.get(LOG_LEVEL, "DEBUG")
        self.app_port = int(os.environ.get(APP_PORT, "80"))
        self.app_host = "0.0.0.0"

        logger.info("DB name: {}, DB username: {}, DB password: {}, DB hostname: {}, DB port: {}"
                    .format(self.db_name, self.db_username, self.db_password, self.db_hostname, self.db_port))

    @classmethod
    def _load_database_credentials_and_type(cls):
        if "_MONGODB_DBNAME" in ''.join(os.environ.keys()):
            logger.debug("Detected MongoDB 3.0 substring in env variables. Assuming this db.")
            db_type = MongoVersion['30']
            return cls._get_service_credentials(db_type)
        elif "_MONGODB_MULTINODE_DBNAME" in ''.join(os.environ.keys()):
            logger.debug("Detected MongoDB 3.0 multi node substring in env variables. Assuming this db.")
            db_type = MongoVersion['30_MULTINODE']
            return cls._get_service_credentials(db_type)
        logger.error("No expected db services found " + str(MongoVersion.values()) + " Exiting...")

    @classmethod
    def _get_service_credentials(cls, db_type):
        try:
            if db_type in [MongoVersion['30'], MongoVersion['26']]:
                dbname_env = '_MONGODB_DBNAME'
                username_env = '_MONGODB_USERNAME'
                password_env = '_MONGODB_PASSWORD'
                hostname_env = '_MONGO_HOSTNAME'
                for variable in os.environ.keys():
                    if variable.endswith(dbname_env):
                        db_name = os.environ[variable]
                        if db_name == '':
                            os.environ[variable] = 'default_db_name'
                            db_name = os.environ[variable]
                    elif variable.endswith(username_env):
                        username = os.environ[variable]
                    elif variable.endswith(password_env):
                        password = os.environ[variable]
                    elif variable.endswith(hostname_env):
                        hostname = os.environ[variable]
                port = MONGODB_SERVER_PORT
                credentials = {
                    'db_type': db_type,
                    'db_name': db_name,
                    'username': username,
                    'password': password,
                    'hostname': hostname,
                    'port': port
                }
                return credentials
            elif db_type == MongoVersion['30_MULTINODE']:
                # TODO: put here parsing of multinode mongodb config when available on TAP 0.9
                pass
        except UnboundLocalError as e:
            raise KeyError("Missing environment variable. Following exception occured: <{}>".format(e))


class ConfigurationError(Exception):
    pass


class NoConfigurationError(Exception):
    pass
