# #
# # Copyright (c) 2016 Intel Corporation
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #    http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #
# import json
# import pytest
# import requests
#
# base_url = "http://10.102.63.199:8080"
#
#
# TEST_RUN_STATES = ["PASS", "FAIL", "IN_PROGRESS"]
# TEST_RESULTS = ["PASS", "FAIL", "ERROR"]
#
#
# @pytest.fixture(scope="module")
# def run_results():
#     test_id = 1
#     headers = {"accept": "application/json"}
#     response = requests.get(url="{}/tests/{}/results".format(base_url, test_id),
#                             headers=headers)
#     assert response.status_code == 200
#     return json.loads(response.text)
#
#
# def test_trigger_tests():
#     response = requests.post(url="{}/tests".format(base_url))
#     response_json = json.loads(response.text)
#     assert isinstance(response_json, dict)
#     assert response_json.get("runId") is not None
#     assert response.status_code == 200
#     assert isinstance(response_json["runId"], int)
#
#
# def test_get_tests():
#     response = requests.get(url="{}/tests".format(base_url))
#     response_json = json.loads(response.text)
#     assert isinstance(response_json, list)
#
#
# def test_run_results_response_type(run_results):
#     assert isinstance(run_results, dict)
#
#
# results_response_test_data = [
#     ("runId", int),
#     ("allTestCount", int),
#     ("testsFinishedCount", int),
#     ("tests", list)
# ]
#
#
# @pytest.mark.parametrize("key,value_type", results_response_test_data)
# def test_results_response(run_results, key, value_type):
#     assert isinstance(run_results[key], value_type)
#
#
# def test_run_results_run_state(run_results):
#     assert run_results.get("state") in TEST_RUN_STATES
#
#
# results_tests_test_data = [
#     ("id", str),
#     ("name", str),
#     ("order", int),
#     ("components", list),
#     ("stacktrace", str)
# ]
#
#
# @pytest.mark.parametrize("key,value_type", results_tests_test_data)
# def test_run_results_test_ids(run_results, key, value_type):
#     tests = run_results.get("tests")
#     fields = [item.get(key) for item in tests]
#     assert len(fields) > 0
#     assert all(isinstance(field, value_type) for field in fields)
#
#
# def test_run_results_test_result(run_results):
#     tests = run_results.get("tests")
#     test_results = [item.get("result") for item in tests]
#     assert len(test_results) > 0
#     assert all(result in TEST_RESULTS for result in test_results)
#
#
#
#
