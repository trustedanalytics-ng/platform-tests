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

import configparser
import os

import teamcity


class TeamCityConfiguration(object):
    _TC_BUILD_PROPERTIES_FILE_ENV_KEY = "TEAMCITY_BUILD_PROPERTIES_FILE"
    _CONFIG_FILE_PATH_KEY = "teamcity.configuration.properties.file"
    _DEFAULT_SECTION = "default"
    _CONFIGURATION = None

    @classmethod
    def _parse_tc_config(cls, path: str) -> dict:
        """
        Parse TeamCity config file and return its options as a dict.
        """
        assert os.path.isfile(path), "No such file {}".format(path)
        with open(path) as f:
            content = f.read()
        # add dummy default section which allows TC config to be read using configparser
        # http://stackoverflow.com/a/2885753
        config_string = "[{}]\n{}".format(cls._DEFAULT_SECTION, content)
        config = configparser.ConfigParser(delimiters="=")
        config.read_string(config_string)
        return {k: v for k, v in config.items(section=cls._DEFAULT_SECTION)}

    @classmethod
    def _initialize_configuration(cls):
        """
        Retrieve path to build properties file from TC env variables.
        Parse the build properties file to retrieve path to configuration properties file.
        Parse the configuration properties file and assign it to cls._CONFIGURATION.

        If the code is running under TC, it is expected that TC environment variables are set and config
        files are present. Otherwise, cls._CONFIGURATION is initialized to an empty dict.
        """

        if cls._CONFIGURATION is None:
            if teamcity.is_running_under_teamcity():
                # Retrieve path to TC build properties file from TC environment variables
                tc_build_properties_file_path = os.environ.get(cls._TC_BUILD_PROPERTIES_FILE_ENV_KEY)
                assert tc_build_properties_file_path is not None,\
                    "No such environment variable {}".format(cls._TC_BUILD_PROPERTIES_FILE_ENV_KEY)

                # parse the file to retrieve path to TC configuration properties file
                tc_build_properties = cls._parse_tc_config(tc_build_properties_file_path)
                config_path = tc_build_properties[cls._CONFIG_FILE_PATH_KEY]
                assert config_path is not None, "Did not find {} option in {}".format(cls._CONFIG_FILE_PATH_KEY,
                                                                                      tc_build_properties_file_path)
                cls._CONFIGURATION = cls._parse_tc_config(config_path)
            else:
                cls._CONFIGURATION = {}

    @classmethod
    def get(cls, name, fallback=None):
        cls._initialize_configuration()
        return cls._CONFIGURATION.get(name, fallback)

    @classmethod
    def getint(cls, name, fallback=-1):
        return int(cls.get(name, fallback))

    @classmethod
    def get_all(cls):
        cls._initialize_configuration()
        return {k.replace(".", "_"): v for k, v in cls._CONFIGURATION.items()}
