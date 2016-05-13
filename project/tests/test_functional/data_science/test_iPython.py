#
# Copyright (c) 2015-2016 Intel Corporation
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

import re

import pytest
from retry import retry

from configuration import config
from modules.constants import TapComponent as TAP
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.service_tools.ipython import iPython
from modules.tap_object_model import Application, ServiceInstance, User
from tests.fixtures.test_data import TestData


logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [components.service_catalog, components.service_exposer]


class iPythonConsole(TapTestCase):

    ATK_PLAN_NAME = "Simple"
    TERMINAL_NO = 0

    @property
    def terminal_no(self):
        """each test will be done in a separate terminal"""
        current_terminal = self.TERMINAL_NO
        self.TERMINAL_NO += 1
        return current_terminal

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_ipython_instance(cls, request, test_org, test_space, admin_user):
        admin_user.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                    roles=User.SPACE_ROLES["developer"])
        cls.step("Create instance of iPython service")
        cls.ipython = iPython(org_guid=test_org.guid, space_guid=test_space.guid)
        cls._assert_ipython_instance_created(cls.ipython.instance, space_guid=test_space.guid, ipython=cls.ipython)
        cls.step("Login into iPython")
        cls.ipython.login()
        request.addfinalizer(lambda: cls.ipython.instance.api_delete())

    @classmethod
    @retry(AssertionError, tries=5, delay=5)
    def _assert_ipython_instance_created(cls, instance, space_guid, ipython):
        cls.step("Get list of service instances and check ipython is on the list")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        if instance not in instances:
            raise AssertionError("ipython instance is not on list")
        cls.step("Get credentials for the new ipython service instance")
        ipython.get_credentials()

    def _find_pattern_in_output(self, ipython_terminal, pattern, eof_pattern):
        output = ipython_terminal.get_output(eof_pattern)
        self.assertIsNotNone(re.search(pattern, str(output)))

    @priority.high
    def test_iPython_terminal(self):
        self.step("Create new ipython terminal")
        terminal = self.ipython.connect_to_terminal(terminal_no=self.terminal_no)
        initial_output = terminal.get_output()
        self.assertTrue(any("#" in item for item in initial_output), "Terminal prompt missing")
        self.step("Check that Python interpreter runs OK in iPython terminal")
        terminal.send_input("python\r")  # Run Python in the terminal
        self._find_pattern_in_output(terminal, "Python", ">>>")

    @priority.high
    def test_iPython_interactive_mode_hello_world(self):
        self.step("Create new notebook in iPython")
        notebook = self.ipython.create_notebook()
        self.step("Check that a simple command is properly handled in iPython")
        notebook.send_input("print('Hello, world!')")
        output = notebook.get_stream_result()
        self.assertEqual(output, "Hello, world!\n")

    @priority.medium
    @pytest.mark.usefixtures("core_space")
    def test_iPython_connect_to_atk_client(self):
        self.step("Get atk app from core space")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(TestData.core_space.guid) if app.name == "atk"),
                       None)
        if atk_app is None:
            raise AssertionError("Atk app not found in core space")
        self.atk_url = atk_app.urls[0]
        self.step("Create new iPython terminal and install atk client")
        terminal = self.ipython.connect_to_terminal(terminal_no=self.terminal_no)
        terminal.send_input("pip2 install http://{}/client\r".format(self.atk_url))
        self.step("Check in terminal output that atk client was successfully installed")
        self._find_pattern_in_output(terminal, "Successfully installed .* trustedanalytics", eof_pattern="#")
        self.step("Create new iPython notebook")
        notebook = self.ipython.create_notebook()
        self.step("import atk client in the notebook")
        notebook.send_input("import trustedanalytics as ta")
        self.assertEqual(notebook.check_command_status(), "ok")
        self.step("Create credentials file using atk client")
        notebook.send_input("ta.create_credentials_file('./cred_file')")
        self.assertIn("URI of the ATK server", notebook.get_prompt_text())
        notebook.send_input(self.atk_url, reply=True)
        self.assertIn("User name", notebook.get_prompt_text())
        notebook.send_input(config.CONFIG["admin_username"], reply=True)
        self.assertIn("", notebook.get_prompt_text())
        notebook.send_input(config.CONFIG["admin_password"], reply=True, obscure_from_log=True)
        self.assertIn("Connect now?", notebook.get_prompt_text())
        notebook.send_input("y", reply=True)
        self.assertIn("Connected.", notebook.get_stream_result())
