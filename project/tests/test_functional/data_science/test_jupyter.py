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

import re

import pytest

import config
from modules.constants import TapComponent as TAP
from modules.markers import components, priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_object_model import Application, ServiceInstance, User
from modules.tap_logger import step
from tests.fixtures import assertions


logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [components.service_catalog, components.service_exposer]


class TestJupyterConsole:

    ATK_PLAN_NAME = "Simple"
    TERMINAL_INDEX = 0

    @pytest.fixture(scope="function")
    def terminal_index(self):
        """Each test will be done in a separate terminal"""
        current_terminal = self.__class__.TERMINAL_INDEX
        self.__class__.TERMINAL_INDEX += 1
        return current_terminal

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_jupyter_instance(cls, class_context, request, test_org, test_space, admin_user):
        admin_user.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                    roles=User.SPACE_ROLES["developer"])
        step("Create instance of Jupyter service")
        cls.jupyter = Jupyter(class_context, org_guid=test_org.guid, space_guid=test_space.guid)
        assertions.assert_in_with_retry(cls.jupyter.instance, ServiceInstance.api_get_list, space_guid=test_space.guid)
        step("Get credentials for the new jupyter service instance")
        cls.jupyter.get_credentials()
        step("Login into Jupyter")
        cls.jupyter.login()
        request.addfinalizer(lambda: cls.jupyter.instance.api_delete())

    @staticmethod
    def _assert_pattern_in_output(jupyter_terminal, pattern):
        output = jupyter_terminal.get_output()
        assert re.search(pattern, str(output)) is not None

    @priority.high
    def test_jupyter_terminal(self, terminal_index):
        step("Create new jupyter terminal")
        terminal = self.jupyter.connect_to_terminal(terminal_no=terminal_index)
        step("Check that Python interpreter runs OK in Jupyter terminal")
        terminal.send_input("python\r")
        self._assert_pattern_in_output(terminal, "Python")
        terminal.ws.close()

    @priority.high
    def test_jupyter_interactive_mode_hello_world(self):
        step("Create new notebook in Jupyter")
        notebook = self.jupyter.create_notebook()
        step("Check that a simple command is properly handled in Jupyter")
        notebook.send_input("print('Hello, world!')")
        output = notebook.get_stream_result()
        assert output[-1] == "Hello, world!\n"
        notebook.ws.close()

    @priority.medium
    def test_jupyter_connect_to_atk_client(self, terminal_index, core_space):
        step("Get atk app from core space")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(core_space.guid)
                        if app.name == "atk"), None)
        if atk_app is None:
            raise AssertionError("Atk app not found in core space")
        atk_url = atk_app.urls[0]
        step("Create new Jupyter terminal and install atk client")
        terminal = self.jupyter.connect_to_terminal(terminal_no=terminal_index)
        terminal.send_input("pip install http://{}/client\r".format(atk_url))
        step("Check in terminal output that atk client was successfully installed")
        self._assert_pattern_in_output(terminal, "Successfully installed trustedanalytics")
        step("Create new Jupyter notebook")
        notebook = self.jupyter.create_notebook()
        step("import atk client in the notebook")
        notebook.send_input("import trustedanalytics as ta")
        assert notebook.check_command_status() == "ok"
        step("Create credentials file using atk client")
        notebook.send_input("ta.create_credentials_file('./cred_file')")
        assert "URI of the ATK server" in notebook.get_prompt_text()
        notebook.send_input(atk_url, reply=True)
        assert "User name" in notebook.get_prompt_text()
        notebook.send_input(config.admin_username, reply=True)
        assert "" in notebook.get_prompt_text()
        notebook.send_input(config.admin_password, reply=True, obscure_from_log=True)
        assert "Connect now?" in notebook.get_prompt_text()
        notebook.send_input("y", reply=True)
        assert "Connected." in str(notebook.get_stream_result())
        notebook.ws.close()
