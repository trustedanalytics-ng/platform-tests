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

from modules.gatling_runner.unittests.package_test_case import PackageTestCase
from modules.gatling_runner.simulation.simulation_name import SimulationName
from modules.gatling_runner.gatling_runner_parameters import GatlingRunnerParameters, \
    GatlingRunnerParametersInvalidPropertyTypeException, GatlingRunnerParametersEmptyPropertyException


class TestGatlingRunnerParameters(PackageTestCase):
    """Unit: GatlingRunnerParameters."""

    SIMULATION_NAME = SimulationName.LOAD_RESOURCES
    PLATFORM = "test.platform.org"
    ORGANIZATION = "test_organization"
    SPACE = "test_space"
    USERNAME = "test_username"
    PASSWORD = "test_password"
    PROXY = "test.proxy"
    PROXY_HTTP_PORT = 911
    PROXY_HTTPS_PORT = 912
    USERS = 10
    USERS_AT_ONCE = 11
    RAMP = 1
    DURATION = 3600
    REPEAT = 50

    def test_init_should_return_valid_object_instance(self):
        config = GatlingRunnerParameters(
            simulation_name=self.SIMULATION_NAME,
            platform=self.PLATFORM,
            organization=self.ORGANIZATION,
            space=self.SPACE,
            username=self.USERNAME,
            password=self.PASSWORD,
            proxy=self.PROXY,
            proxy_http_port=self.PROXY_HTTP_PORT,
            proxy_https_port=self.PROXY_HTTPS_PORT,
            users=self.USERS,
            users_at_once=self.USERS_AT_ONCE,
            ramp=self.RAMP,
            duration=self.DURATION,
            repeat=self.REPEAT
        )
        self.assertIsInstance(config, GatlingRunnerParameters, "Invalid instance class.")
        self.assertEqual(self.SIMULATION_NAME, config.simulation_name)
        self.assertEqual(self.PLATFORM, config.platform)
        self.assertEqual(self.ORGANIZATION, config.organization)
        self.assertEqual(self.SPACE, config.space)
        self.assertEqual(self.USERNAME, config.username)
        self.assertEqual(self.PASSWORD, config.password)
        self.assertEqual(self.PROXY, config.proxy)
        self.assertEqual(self.PROXY_HTTP_PORT, config.proxy_http_port)
        self.assertEqual(self.PROXY_HTTPS_PORT, config.proxy_https_port)
        self.assertEqual(self.USERS, config.users)
        self.assertEqual(self.USERS_AT_ONCE, config.users_at_once)
        self.assertEqual(self.RAMP, config.ramp)
        self.assertEqual(self.DURATION, config.duration)
        self.assertEqual(self.REPEAT, config.repeat)

    def test_init_should_return_exception_when_invalid_property_type(self):
        self.assertRaises(
            GatlingRunnerParametersInvalidPropertyTypeException,
            GatlingRunnerParameters,
            "Undefined"
        )

    def test_init_should_return_exception_when_empty_property_value(self):
        self.assertRaises(
            GatlingRunnerParametersEmptyPropertyException,
            GatlingRunnerParameters,
            ""
        )
