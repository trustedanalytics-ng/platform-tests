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
import pytest
from retry import retry

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
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

class TestJupyterConsole:

    @staticmethod
    @pytest.fixture(scope="class")
    def jupyter_instance(class_context, admin_user):
        step("Create instance of Jupyter service")
        jupyter = Jupyter(class_context)
        assertions.assert_in_with_retry(jupyter.instance, ServiceInstance.get_list)
        return jupyter

    @pytest.mark.bugs("DPNG-15388 Missing example files in jupyter")
    @priority.medium
    @pytest.mark.parametrize("notebook_path", NOTEBOOKS_PATHS[1:])
    def test_spark_tk_in_jupyter(self, jupyter_instance, notebook_path):
        """
        <b>Description:</b>
        Checks if notebooks scripts can be RUN.

        <b>Input data:</b>
        1. Jupyter instance.
        2. Notebooks paths.

        <b>Expected results:</b>
        Test passes when all scripts are executed.

        <b>Steps:</b>
        1. Run scripts from all notebooks except the first one.
        2. Verify that scripts run properly.
        """
        step("Run {} notebook".format(notebook_path))
        self.run_cells(notebook=jupyter_instance.create_notebook(),
                       cells=jupyter_instance.get_notebook_source(notebook_path))

    @pytest.mark.bugs("DPNG-15388 Missing example files in jupyter")
    @priority.medium
    def test_spark_tk_readme_in_jupyter(self, jupyter_instance):
        """
        <b>Description:</b>
        Checks if readme scripts can be RUN.

        <b>Input data:</b>
        1. Jupyter instance.
        2. Notebook paths.

        <b>Expected results:</b>
        Test passes when script is executed.

        <b>Steps:</b>
        1. Run README notebook.
        2. Run SparkContext in local mode.
        3. Verify that script run properly.
        4. Run SparkContext in yarn-client mode.
        5. Verify that script run properly.
        """
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
