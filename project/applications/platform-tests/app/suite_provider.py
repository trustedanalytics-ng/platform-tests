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

import ast
import os

import dateutil.parser
import math


class SuiteProvider(object):
    """Available test suites provider"""

    TEST_PREFIX = "test_"

    SUITE_NAME = "System Operations Test Suite"

    SUITES = [{
        "id": "project.tests.test_smoke.test_functional",
        "title": SUITE_NAME,
    }]

    @classmethod
    def get_list(cls, last_runs) -> list:
        """Return list of available test suites"""
        suites = []
        for s in cls.SUITES:
            s["tests"] = cls._get_tests(s)
            s["approxRunTime"] = cls._get_average_run_time(last_runs)
            suites.append(s)
        return suites

    @classmethod
    def _get_tests(cls, suite: dict):
        """Get suite available tests"""
        suite_file_name = "{}.py".format(str(suite["id"]).replace('.', os.path.sep))
        with open(suite_file_name) as f:
            file_contents = f.read()
        module = ast.parse(file_contents)
        functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
        docs = [ast.get_docstring(f) for f in functions if f.name.startswith(cls.TEST_PREFIX)]
        return docs

    @classmethod
    def _get_average_run_time(cls, suite_documents):
        """Get suite average run time"""
        counter = 0
        execution_time = 0.0
        for suite_document in suite_documents:
            counter += 1
            start_date = dateutil.parser.parse(str(suite_document['start_date']))
            end_date = dateutil.parser.parse(str(suite_document['end_date']))
            time_taken = end_date - start_date
            execution_time += time_taken.seconds
        if counter == 0:
            return "30 Minutes"
        execution_time = execution_time / counter
        minutes = math.floor(execution_time / 60)
        seconds = int(execution_time - (minutes * 60))
        return "{} Minutes {} Seconds".format(minutes, seconds)
