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


import logging
import os

logging.basicConfig()
logger = logging.getLogger(__name__)

# environment variables to set
LOG_LEVEL = "LOG_LEVEL"
APP_PORT = "APP_PORT"

DB_MYSQL = "mysql56"
DB_POSTGRESQL = "postgresql93"

PORTS = {DB_POSTGRESQL: "5432",
         DB_MYSQL: "3306"}
SUPPORTED_SERVICES = {DB_POSTGRESQL: "postgresql+pg8000",
                      DB_MYSQL: "mysql+mysqlconnector"}


class ConfigurationError(Exception):
    pass


class Config(object):

    def __init__(self):

        """
        Reads configuration from environment variables.
        """

        credentials = self._load_bound_database()
        try:
            self.db_type = credentials[0].encode('ascii', 'ignore')
            self.db_name = credentials[1].encode('ascii', 'ignore')
            self.db_username = credentials[2].encode('ascii', 'ignore')
            self.db_password = credentials[3].encode('ascii', 'ignore')
            self.db_hostname = credentials[4].encode('ascii', 'ignore')
        except KeyError as e:
            raise ConfigurationError("Missing {} in service credentials".format(e))
        self.db_port = int(credentials[5])
        self.app_port = int(os.environ.get(APP_PORT, "80"))
        self.app_host = "0.0.0.0"
        self.log_level = os.environ.get(LOG_LEVEL, "DEBUG")
        logger.info("DB name: {}, DB username: {}, DB password: {}, DB hostname: {}, DB port: {}"
                    .format(self.db_name, self.db_username, self.db_password, self.db_hostname, self.db_port))

    @classmethod
    def _get_service_credentials(cls, type, prefix):
        try:
            service_type = type
            dbname_env = '_' + prefix + '_DBNAME'
            username_env = '_' + prefix + '_USERNAME'
            password_env = '_' + prefix + '_PASSWORD'
            hostname_env = '_' + prefix + '_HOSTNAME'
            for variable in os.environ.keys():
                if variable.endswith(dbname_env):
                    dbname = os.environ[variable]
                elif variable.endswith(username_env):
                    username = os.environ[variable]
                elif variable.endswith(password_env):
                    password = os.environ[variable]
                elif variable.endswith(hostname_env):
                    hostname = os.environ[variable]
            port = PORTS[type]
            credentials = [service_type, dbname, username, password, hostname, port]

        except UnboundLocalError as e:
            raise ConfigurationError("Missing environment variable. Following exception occured: <{}>".format(e))
        return credentials

    @classmethod
    def _load_bound_database(cls):
        if "_POSTGRES_DBNAME" in ''.join(os.environ.keys()):
            logger.debug("Detected POSTGRES substring in env variables. Assuming this db.")
            return cls._get_service_credentials(DB_POSTGRESQL, "POSTGRES")
        if "_MYSQL_DBNAME" in ''.join(os.environ.keys()):
            logger.debug("Detected MYSQL substring in env variables. Assuming this db.")
            return cls._get_service_credentials(DB_MYSQL, "MYSQL")
        logger.error("No expected db services found " + str(SUPPORTED_SERVICES.keys()) + " Exiting...")
        exit(1)
