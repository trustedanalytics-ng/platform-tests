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
# import json
# import os
#
# import pytest
#
# from app.config import Config, IncorrectConfigurationException, DatabaseConfig


# config_data = {
#     "VCAP_SERVICES": {"mongodb26": [
#         {"credentials":
#              {
#                  "dbname": "test_name", "hostname": "test_hostname", "password": "test_password",
#                  "username": "test_username", "port": 12345
#              }
#          }
#     ]},
#     "VCAP_APPLICATION": {"uris": ["platform-tests.test-domain.com"]},
#     "VCAP_APP_PORT": 1234,
#     "ADMIN_USERNAME": "test_admin_username",
#     "ADMIN_PASSWORD": "test_admin_password",
#     "REFERENCE_ORG": "test_org",
#     "REFERENCE_SPACE": "test_space"
# }
# required_environment_variables = ["VCAP_APPLICATION", "ADMIN_USERNAME", "ADMIN_PASSWORD"]
#
#
# def set_environment_variables(config_dict, keys=None):
#     if keys is None:
#         keys = config_dict.keys()
#     for key in keys:
#         value = config_dict[key]
#         if isinstance(value, dict):
#             value = json.dumps(value)
#         os.environ[key] = str(value)
#
#
# def unset_variables():
#     for env_var_name in config_data.keys():
#         if os.environ.get(env_var_name) is not None:
#             del os.environ[env_var_name]
#
#
# @pytest.fixture(scope="function")
# def full_configuration_config(request):
#     request.addfinalizer(unset_variables)
#     set_environment_variables(config_data)
#     return DatabaseConfig()
#
#
# @pytest.fixture(scope="function")
# def minimal_configuration_config(request):
#     request.addfinalizer(unset_variables)
#     set_environment_variables(config_data, required_environment_variables)
#     return DatabaseConfig()
#
#
# @pytest.mark.parametrize("config_key_name,config_value", [
#     ("dbname", config_data["VCAP_SERVICES"]["mongodb26"][0]["credentials"]["dbname"]),
#     ("hostname", config_data["VCAP_SERVICES"]["mongodb26"][0]["credentials"]["hostname"]),
#     ("password", config_data["VCAP_SERVICES"]["mongodb26"][0]["credentials"]["password"]),
#     ("username", config_data["VCAP_SERVICES"]["mongodb26"][0]["credentials"]["username"]),
#     ("port", config_data["VCAP_SERVICES"]["mongodb26"][0]["credentials"]["port"]),
#     # ("app_port", config_data["VCAP_APP_PORT"]),
#     # ("admin_username", config_data["ADMIN_USERNAME"]),
#     # ("admin_password", config_data["ADMIN_PASSWORD"]),
#     # ("reference_org", config_data["REFERENCE_ORG"]),
#     # ("reference_space", config_data["REFERENCE_SPACE"]),
#     # ("tap_domain", "test-domain.com")
# ])
# def test_full_custom_configuration(config_key_name, config_value, full_configuration_config):
#     assert getattr(full_configuration_config, config_key_name) == config_value
#
#
# @pytest.mark.parametrize("config_key_name,config_value", [
#     ("dbname", DatabaseConfig._default_config["dbname"]),
#     ("hostname", DatabaseConfig._default_config["hostname"]),
#     ("password", None),
#     ("username", None),
#     ("port", DatabaseConfig._default_config["port"]),
#     # ("app_port", DatabaseConfig._DatabaseConfig__default_config["app_port"]),
#     # ("reference_org", DatabaseConfig._DatabaseConfig__default_config["reference_org"]),
#     # ("reference_space", DatabaseConfig._DatabaseConfig__default_config["reference_space"]),
#     #
#     # ("tap_domain", "test-domain.com"),
#     # ("admin_username", config_data["ADMIN_USERNAME"]),
#     # ("admin_password", config_data["ADMIN_PASSWORD"]),
# ])
# def test_minimal_configuration(config_key_name, config_value, minimal_configuration_config):
#     assert getattr(minimal_configuration_config, config_key_name) == config_value


# def test_no_configuration():
#     config = Config()
#     with pytest.raises(IncorrectConfigurationException):
#         config.get("test_key")


# @pytest.fixture(scope="function")
# def incorrect_vcap_services(request):
#     request.addfinalizer(unset_variables)
#     env_variables = config_data.copy()
#     env_variables["VCAP_SERVICES"] = {"mongodb26": None}
#     set_environment_variables(env_variables)
#
# def test_incorrect_vcap_services(incorrect_vcap_services):
#     config = Config()
#     with pytest.raises(IncorrectConfigurationException):
#         config.get("test_key")

#
# @pytest.fixture(scope="function")
# def incorrect_vcap_application(request):
#     request.addfinalizer(unset_variables)
#     env_variables = config_data.copy()
#     env_variables["VCAP_APPLICATION"] = {"uris": "platform-tests.test-domain.com"}
#     set_environment_variables(env_variables)
#
# def test_incorrect_vcap_application(incorrect_vcap_application):
#     config = Config()
#     with pytest.raises(IncorrectConfigurationException):
#         config.get("test_key")