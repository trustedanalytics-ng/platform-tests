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

from retry import retry

from configuration import config
from modules.constants import TapComponent as TAP
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, priority
from modules.service_tools.ipython import iPython
from modules.tap_object_model import Application, Organization, ServiceInstance, Space, User


@log_components()
@components(TAP.service_catalog, TAP.service_exposer)
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
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Get reference space")
        _, cls.ref_space = Organization.get_ref_org_and_space()
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)
        admin_user = User.get_admin()
        admin_user.api_add_to_space(space_guid=cls.test_space.guid, org_guid=cls.test_org.guid,
                                    roles=User.SPACE_ROLES["developer"])
        cls.step("Create instance of iPython service")
        cls.ipython = iPython(org_guid=cls.test_org.guid, space_guid=cls.test_space.guid)
        cls._assert_ipython_instance_created(cls.ipython.instance, space_guid=cls.test_space.guid, ipython=cls.ipython)
        cls.step("Login into iPython")
        cls.ipython.login()

    @classmethod
    @retry(AssertionError, tries=5, delay=5)
    def _assert_ipython_instance_created(cls, instance, space_guid, ipython):
        cls.step("Get list of service instances and check ipython is on the list")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        if instance not in instances:
            raise AssertionError("ipython instance is not on list")
        cls.step("Get credentials for the new ipython service instance")
        ipython.get_credentials()

    @retry(AssertionError, tries=5, delay=5)
    def _assert_atk_client_is_installed(self, ipython_terminal):
        self.step("Check in terminal output that atk client was successfully installed")
        success_pattern = "Successfully installed .* trustedanalytics"
        output = ipython_terminal.get_output()
        self.assertIsNotNone(re.search(success_pattern, output[-2]))
        self.assertIn("#", output[-1])

    @priority.high
    def test_iPython_terminal(self):
        self.step("Create new ipython terminal")
        terminal = self.ipython.connect_to_terminal(terminal_no=self.terminal_no)
        initial_output = terminal.get_output()
        self.assertTrue(any("#" in item for item in initial_output), "Terminal prompt missing")
        self.step("Check that Python interpreter runs OK in iPython terminal")
        terminal.send_input("python\r")  # Run Python in the terminal
        output = terminal.get_output()
        self.assertIn("Python", output[-2])
        self.assertIn(">>>", output[-1])

    @priority.high
    def test_iPython_interactive_mode_hello_world(self):
        self.step("Create new notebook in iPython")
        notebook = self.ipython.create_notebook()
        self.step("Check that a simple command is properly handled in iPython")
        notebook.send_input("print('Hello, world!')")
        output = notebook.get_stream_result()
        self.assertEqual(output, "Hello, world!\n")

    @priority.medium
    def test_iPython_connect_to_atk_client(self):
        self.step("Get atk app from seedspace")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(self.ref_space.guid) if app.name == "atk"), None)
        if atk_app is None:
            raise AssertionError("Atk app not found in seedspace")
        self.atk_url = atk_app.urls[0]
        self.step("Create new iPython terminal and install atk client")
        terminal = self.ipython.connect_to_terminal(terminal_no=self.terminal_no)
        terminal.send_input("pip2 install http://{}/client\r".format(self.atk_url))
        self._assert_atk_client_is_installed(terminal)
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
