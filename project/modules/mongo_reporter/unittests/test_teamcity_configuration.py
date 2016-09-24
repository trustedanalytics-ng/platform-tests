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
from unittest import mock

import pytest

from modules.mongo_reporter._teamcity_configuration import TeamCityConfiguration


class TestTeamCityConfiguration:
    FIXTURES_PATH = os.path.join("modules", "mongo_reporter", "unittests", "fixtures")
    EXAMPLE_TC_CONFIG_PATH = os.path.join(FIXTURES_PATH, "example_tc_config_file")
    EXAMPLE_TC_BUILD_FILE = os.path.join(FIXTURES_PATH, "example_tc_build_properties_file")
    assert os.path.isfile(EXAMPLE_TC_CONFIG_PATH)
    assert os.path.isfile(EXAMPLE_TC_BUILD_FILE)
    BUILD_CONFIG_VALUE_TO_REPLACE = "{****replace_me****}"
    TEST_CONFIG_ENTRY = ("test.key", "test value")
    TEST_CONFIG_ENTRY_INT = ("test.key.int", 4)

    def _replace_in_file(self, file_path, old, new):
        with open(file_path, "r+") as f:
            content = f.read().replace(old, new)
            f.seek(0)
            f.write(content)
            f.truncate()

    def _set_build_properties_file_env_variable(self, value=None):
        if value is None:
            value = self.EXAMPLE_TC_BUILD_FILE
        os.environ[TeamCityConfiguration._TC_BUILD_PROPERTIES_FILE_ENV_KEY] = value

    @pytest.fixture(scope="class", autouse=True)
    def substitute_path(self, request):
        self._replace_in_file(self.EXAMPLE_TC_BUILD_FILE, old=self.BUILD_CONFIG_VALUE_TO_REPLACE,
                              new=self.EXAMPLE_TC_CONFIG_PATH)
        request.addfinalizer(lambda: self._replace_in_file(self.EXAMPLE_TC_BUILD_FILE,
                                                           old=self.EXAMPLE_TC_CONFIG_PATH,
                                                           new=self.BUILD_CONFIG_VALUE_TO_REPLACE))

    @pytest.fixture(scope="function", autouse=True)
    def restore_config(self):
        TeamCityConfiguration._CONFIGURATION = None

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_env_variable(self, request):
        def fin():
            if TeamCityConfiguration._TC_BUILD_PROPERTIES_FILE_ENV_KEY in os.environ:
                del os.environ[TeamCityConfiguration._TC_BUILD_PROPERTIES_FILE_ENV_KEY]
        request.addfinalizer(fin)

    @pytest.mark.parametrize("config_file_path", (EXAMPLE_TC_BUILD_FILE, EXAMPLE_TC_CONFIG_PATH))
    def test_config_from_file(self, config_file_path):
        parsed_config = TeamCityConfiguration._parse_tc_config(config_file_path)
        assert isinstance(parsed_config, dict)
        assert len(parsed_config) > 0

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: False)
    def test_initialize_configuration_not_under_tc(self):
        TeamCityConfiguration._initialize_configuration()
        assert TeamCityConfiguration._CONFIGURATION == {}

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    def test_initialize_configuration_under_tc(self):
        self._set_build_properties_file_env_variable()
        TeamCityConfiguration._initialize_configuration()
        assert len(TeamCityConfiguration._CONFIGURATION) > 0

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    def test_initialize_configuration_tc_env_var_not_set(self):
        with pytest.raises(AssertionError) as e:
            TeamCityConfiguration._initialize_configuration()
        assert "No such environment variable" in e.value.msg

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    def test_initialize_configuration_not_existing_tc_build_file(self):
        self._set_build_properties_file_env_variable(value="idontexist")
        with pytest.raises(AssertionError) as e:
            TeamCityConfiguration._initialize_configuration()
        assert "No such file" in e.value.msg

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    def test_get(self):
        self._set_build_properties_file_env_variable()
        value = TeamCityConfiguration.get(self.TEST_CONFIG_ENTRY[0])
        assert value == self.TEST_CONFIG_ENTRY[1]

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    def test_getint(self):
        self._set_build_properties_file_env_variable()
        value = TeamCityConfiguration.getint(self.TEST_CONFIG_ENTRY_INT[0])
        assert isinstance(value, int)
        assert value == self.TEST_CONFIG_ENTRY_INT[1]

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    @pytest.mark.parametrize("tested_method,default_fallback,test_fallback",
                             ((TeamCityConfiguration.get, None, "fallback"),
                              (TeamCityConfiguration.getint, -1, 123)))
    def test_get_not_existing_key(self, tested_method, default_fallback, test_fallback):
        self._set_build_properties_file_env_variable()
        value = tested_method("i.dont.exist")
        assert value == default_fallback
        value = tested_method("me.neither", fallback=test_fallback)
        assert value == test_fallback

    @mock.patch("modules.mongo_reporter._teamcity_configuration.teamcity.is_running_under_teamcity", lambda: True)
    def test_get_all(self):
        self._set_build_properties_file_env_variable()
        values = TeamCityConfiguration.get_all()
        assert isinstance(values, dict)
        assert len(values) > 0
        assert all("." not in k for k in values), "Keys are not escaped"
        assert self.TEST_CONFIG_ENTRY[0].replace(".", "_") in values
        assert values [self.TEST_CONFIG_ENTRY[0].replace(".", "_")] == self.TEST_CONFIG_ENTRY[1]