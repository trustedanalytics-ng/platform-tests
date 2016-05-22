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


# need to set required variables
os.environ["PT_TAP_DOMAIN"] = "test"
os.environ["PT_ADMIN_PASSWORD"] = "test"

import config


@pytest.fixture(scope="function")
def env_key_name(request):
    key_name = "PT_TEST_VARIABLE"

    def fin():
        if key_name in os.environ:
            del os.environ[key_name]
    request.addfinalizer(fin)

    return key_name


def test_accessing_non_existing_value_causes_attribute_error():
    with pytest.raises(AttributeError):
        config.kitten


def test_get_int(env_key_name):
    expected_value = 5
    os.environ[env_key_name] = str(expected_value)
    value = config.get_int(env_key_name)
    assert value == expected_value


def test_get_int_where_env_value_is_not_set(env_key_name):
    value = config.get_int(env_key_name)
    assert value is None


def test_get_int_incorrect_env_setting(env_key_name):
    os.environ[env_key_name] = "kitten"
    with pytest.raises(ValueError):
        config.get_int(env_key_name)


@pytest.mark.parametrize("env_value,expected_value", (("true", True), ("TRUE", True), ("True", True),
                                                      ("false", False), ("FALSE", False), ("False", False)))
def test_get_bool_true(env_key_name, env_value, expected_value):
    os.environ[env_key_name] = env_value
    value = config.get_bool(env_key_name)
    assert value == expected_value


def test_get_bool_where_env_variable_is_not_set(env_key_name):
    value = config.get_bool(env_key_name)
    assert value is None


def test_get_bool_incorrect_env_setting(env_key_name):
    os.environ[env_key_name] = "kitten"
    with pytest.raises(ValueError):
        config.get_bool(env_key_name)


def test_empty_env_variable_is_deleted(env_key_name):
    os.environ[env_key_name] = ""
    config._delete_empty_env_variables()
    assert os.environ.get(env_key_name) is None



def test_assert_config_variable_set():
    with mock.patch.object(config, "tap_domain", "abc"):
        config._assert_config_value_set("tap_domain")


def test_assert_config_variable_set_when_value_is_none():
    with mock.patch.object(config, "tap_domain", None):
        with pytest.raises(AssertionError):
            config._assert_config_value_set("tap_domain")


def test_assert_config_variable_set_when_not_set():
    with pytest.raises(AssertionError):
        config._assert_config_value_set("non_existing_variable")


