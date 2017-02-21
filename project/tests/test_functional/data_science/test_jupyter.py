#
# Copyright (c) 2016 - 2017 Intel Corporation
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

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from tests.fixtures import assertions

logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.service_exposer)]

class TestJupyterConsole:

    TERMINAL_INDEX = 0

    @pytest.fixture(scope="function")
    def terminal_index(self):
        """Each test will be done in a separate terminal"""
        current_terminal = self.__class__.TERMINAL_INDEX
        self.__class__.TERMINAL_INDEX += 1
        return current_terminal

    @staticmethod
    @pytest.fixture(scope="class")
    def jupyter_instance(class_context, admin_user):
        step("Create instance of Jupyter service")
        jupyter = Jupyter(class_context)
        assertions.assert_in_with_retry(jupyter.instance, ServiceInstance.get_list)
        return jupyter

    @staticmethod
    def _assert_pattern_in_output(jupyter_terminal, pattern):
        output = jupyter_terminal.get_output()
        assert re.search(pattern, str(output)) is not None

    @priority.high
    def test_jupyter_terminal(self, jupyter_instance, terminal_index):
        """
        <b>Description:</b>
        Checks if Python interpreter works in newly created Jupyter terminal.

        <b>Input data:</b>
        1. Jupyter instance
        2. Terminal index

        <b>Expected results:</b>
        Test passes when Python interpreter works in Jupyter terminal.

        <b>Steps:</b>
        1. Create new Jupyter terminal
        2. Start python interpreter.
        3. Verify that Python interpreter runs.
        """
        step("Create new jupyter terminal")
        terminal = jupyter_instance.connect_to_terminal(terminal_no=terminal_index)
        step("Check that Python interpreter runs OK in Jupyter terminal")
        terminal.send_input("python\r")
        self._assert_pattern_in_output(terminal, "Python")
        terminal.ws.close()

    @priority.high
    def test_jupyter_interactive_mode_hello_world(self, jupyter_instance):
        """
        <b>Description:</b>
        Checks if a simple command is properly handled in newly created Jupyter notebook.

        <b>Input data:</b>
        1. Jupyter instance.
        2. Python command.

        <b>Expected results:</b>
        Test passes when Python command works in Jupyter notebook.

        <b>Steps:</b>
        1. Create new notebook in Jupyter.
        2. Send print command to the notebook.
        3. Check if Python command works properly.
        """
        step("Create new notebook in Jupyter")
        notebook = jupyter_instance.create_notebook()
        step("Check that a simple command is properly handled in Jupyter")
        notebook.send_input("print('Hello, world!')")
        output = notebook.get_stream_result()
        assert output[-1] == "Hello, world!\n"
        notebook.ws.close()
