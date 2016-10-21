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
from retry import retry

import config
from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, User
from tests.fixtures import assertions

logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.service_exposer)]

NOTEBOOKS_PATHS = ["examples/spark/{}.ipynb".format(filename) for filename in ("README",
                                                                               "pyspark-dataframe-basics",
                                                                               "pyspark-kmeans",
                                                                               "pyspark-linear-regression",
                                                                               "pyspark-rdd-basics",
                                                                               "pyspark-streaming-wordcount",
                                                                               "spark-sql-example")]

@pytest.mark.skip(reason="DPNG-8807 Adjust test_jupyter tests to TAP NG")
class TestJupyterConsole:

    ATK_PLAN_NAME = "Simple"
    TERMINAL_INDEX = 0

    @pytest.fixture(scope="function")
    def terminal_index(self):
        """Each test will be done in a separate terminal"""
        current_terminal = self.__class__.TERMINAL_INDEX
        self.__class__.TERMINAL_INDEX += 1
        return current_terminal

    @staticmethod
    @pytest.fixture(scope="class")
    def jupyter_instance(class_context, test_org, test_space, admin_user):
        admin_user.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                    roles=User.SPACE_ROLES["developer"])
        step("Create instance of Jupyter service")
        jupyter = Jupyter(class_context)
        assertions.assert_in_with_retry(jupyter.instance, ServiceInstance.api_get_list, space_guid=test_space.guid)
        step("Get credentials for the new jupyter service instance")
        jupyter.get_credentials()
        step("Login into Jupyter")
        jupyter.login()
        return jupyter

    @staticmethod
    def _assert_pattern_in_output(jupyter_terminal, pattern):
        output = jupyter_terminal.get_output()
        assert re.search(pattern, str(output)) is not None

    @priority.high
    def test_jupyter_terminal(self, jupyter_instance, terminal_index):
        step("Create new jupyter terminal")
        terminal = jupyter_instance.connect_to_terminal(terminal_no=terminal_index)
        step("Check that Python interpreter runs OK in Jupyter terminal")
        terminal.send_input("python\r")
        self._assert_pattern_in_output(terminal, "Python")
        terminal.ws.close()

    @priority.high
    def test_jupyter_interactive_mode_hello_world(self, jupyter_instance):
        step("Create new notebook in Jupyter")
        notebook = jupyter_instance.create_notebook()
        step("Check that a simple command is properly handled in Jupyter")
        notebook.send_input("print('Hello, world!')")
        output = notebook.get_stream_result()
        assert output[-1] == "Hello, world!\n"
        notebook.ws.close()

    @priority.medium
    def test_connect_to_atk_from_jupyter_using_server_atk_client(self, jupyter_instance, terminal_index, core_space):
        step("Get atk app from core space")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(core_space.guid)
                        if app.name == "atk"), None)
        if atk_app is None:
            raise AssertionError("Atk app not found in core space")
        atk_url = atk_app.urls[0]
        step("Create new Jupyter terminal and install atk client")
        terminal = jupyter_instance.connect_to_terminal(terminal_no=terminal_index)
        terminal.send_input("pip install http://{}/client\r".format(atk_url))
        step("Check in terminal output that atk client was successfully installed")
        self._assert_pattern_in_output(terminal, "Successfully installed trustedanalytics")
        step("Create new Jupyter notebook")
        notebook = jupyter_instance.create_notebook()
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

    @priority.medium
    @pytest.mark.parametrize("notebook_path", NOTEBOOKS_PATHS[1:])
    def test_spark_tk_in_jupyter(self, jupyter_instance, notebook_path):
        step("Run {} notebook".format(notebook_path))
        self.run_cells(notebook=jupyter_instance.create_notebook(),
                       cells=jupyter_instance.get_notebook_source(notebook_path))

    @priority.medium
    def test_spark_tk_readme_in_jupyter(self, jupyter_instance):
        readme_path = NOTEBOOKS_PATHS[0]
        step("Run README notebook")
        cells = jupyter_instance.get_notebook_source(readme_path)
        step("Run SparkContext in local mode")
        self.run_cells(notebook=jupyter_instance.create_notebook(),
                       cells=cells[:4])
        step("Run SparkContext in yarn-client mode")
        self.run_cells(notebook=jupyter_instance.create_notebook(),
                       cells=cells[5:])

    @classmethod
    def run_cells(cls, notebook, cells):
        for i, cell in enumerate(cells, start=1):
            step("Running {} cell".format(i))
            notebook.send_input(cell)
            cls.assert_command_status_ok(notebook)

    @staticmethod
    @retry((StopIteration, AssertionError), tries=20, delay=3)
    def assert_command_status_ok(notebook):
        assert notebook.check_command_status() == "ok"
