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

import json
from unittest import mock

from . import common

common.set_environment_for_config()
from app.main import TestSuite, app
from app.model import TestSuiteModel

TEST_RUN_STATES = ["PASS", "FAIL", "IN_PROGRESS"]
NO_STACKTRACE_TEST_RESULTS = ["PASS", "SKIP"]
STACKTRACE_TEST_RESULTS = ["ERROR", "FAIL"]
TEST_RESULTS = NO_STACKTRACE_TEST_RESULTS + STACKTRACE_TEST_RESULTS


mock_suite_collection = common.MockCollection()
run_document = common.MockCollection.get_example_run_document()
mock_suite_collection.insert_one(run_document)



# result_document = common.MockCollection.get_example_test_document(run_document["_id"])
#
# TestResultModel._collection.insert_one(result_document)
#
#
# TestSuiteModel._collection = common.MockCollection()
# TestResultModel._collection = common.MockCollection()
#
#
# @mock.patch.object(TestSuiteModel, "_collection")
# @pytest.fixture(scope="module")
# def mock_run():
#
#     return run_document["_id"]


# @pytest.fixture(scope="module")
# def one_suite_results():
#     with app.test_request_context():
#         test_results = TestSuiteResults()
#         response = test_results.get(suite_id=suite_id)
#     return json.loads(response.data.decode())


# @pytest.fixture(scope="module")
# def all_test_results():
#     with app.test_request_context():
#         tests = TestSuite()
#         response = tests.get()
#     return json.loads(response.data.decode())


# def test_trigger_tests():
#     assert False, "How to test this?"

@mock.patch.object(TestSuiteModel, "_collection", mock_suite_collection)
def test_get_tests():
    with app.test_request_context():
        tests = TestSuite()
        response = tests.get()
    all_test_results = json.loads(response.data.decode())
    assert isinstance(all_test_results, list)


# def test_run_results_response_type(one_run_results):
#     assert isinstance(one_run_results, dict)
#
#
# results_response_test_data = [
#     ("suiteId", str),
#     ("testsAll", int),
#     ("testsFinished", int),
#     ("tests", list)
# ]
#
#
# @pytest.mark.parametrize("key,value_type", results_response_test_data)
# def test_results_response(one_suite_results, key, value_type):
#     assert isinstance(one_suite_results[key], value_type)
#
#
# def test_run_results_run_state(one_run_results):
#     assert one_run_results.get("state") in TEST_RUN_STATES
#
#
# results_tests_test_data = [
#     ("id", str),
#     ("name", str),
#     ("order", int),
#     ("components", list)
# ]
#
#
# @pytest.mark.parametrize("key,value_type", results_tests_test_data)
# def test_run_results_test_ids(one_run_results, key, value_type):
#     tests = one_run_results.get("tests")
#     fields = [item.get(key) for item in tests]
#     assert len(fields) > 0
#     assert all(isinstance(field, value_type) for field in fields)
#
#
# def test_run_results_stack_trace(one_run_results):
#     for test in one_run_results.get("tests"):
#         if test["result"] in NO_STACKTRACE_TEST_RESULTS:
#             assert test.get("stacktrace") is None
#         elif test["result"] in STACKTRACE_TEST_RESULTS:
#             assert isinstance(test["stacktrace"], str)
#
#
# def test_run_results_test_result(one_run_results):
#     tests = one_run_results.get("tests")
#     test_results = [item.get("result") for item in tests]
#     assert len(test_results) > 0
