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


class Config(object):
    """Main package configuration."""

    ENV_PREFIX_BOUND_ORIENTDB_NAME = "SERVICES_BOUND_ORIENTDB"
    ENV_SUFFIX_ORIENTDB_HOSTNAME = "ORIENTDB_HOSTNAME"
    ENV_SUFFIX_ORIENTDB_PORT = "ORIENTDB_BINARY_PORT"
    ENV_SUFFIX_ORIENTDB_USERNAME = "ORIENTDB_USERNAME"
    ENV_SUFFIX_ORIENTDB_PASSWORD = "ORIENTDB_ROOT_PASSWORD"

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
        service_name = Config._get_env_var_by_prefix(Config.ENV_PREFIX_BOUND_ORIENTDB_NAME)
        var_prefix = service_name.upper().replace('-', '_')
        self.db_hostname = Config._get_env_var("{}_{}".format(var_prefix, Config.ENV_SUFFIX_ORIENTDB_HOSTNAME))
        self.db_port = int(Config._get_env_var("{}_{}".format(var_prefix, Config.ENV_SUFFIX_ORIENTDB_PORT)))
        self.db_username = Config._get_env_var("{}_{}".format(var_prefix, Config.ENV_SUFFIX_ORIENTDB_USERNAME))
        self.db_password = Config._get_env_var("{}_{}".format(var_prefix, Config.ENV_SUFFIX_ORIENTDB_PASSWORD))

    @classmethod
    def _get_env_var(cls, varname):
        """Get variable from environment."""
        try:
            var = os.environ[varname]
        except KeyError:
            raise MissingConfigurationError("Environment variable '{}' is missing.".format(varname))
        return var

    @classmethod
    def _get_env_var_by_prefix(cls, var_prefix):
        """Get single environment variable that starts with with var_prefix"""
        results = {}
        for key,val in os.environ.items():
            if key.startswith(var_prefix):
                results[key] = val
        if not results:
            raise MissingConfigurationError("Missing environment variable: no variable starts with prefix '{}'.".format(var_prefix))
        if len(results) > 1:
            raise MissingConfigurationError("Too many environment variables starting with prefix '{}': {}.".format(var_prefix, list(results.keys())))
        return results.values()[0]


class MissingConfigurationError(Exception):
    pass
