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

import time

import config
from modules.http_calls.platform import platform_tests


class TestRun:

    IN_PROGRESS = "IN_PROGRESS"

    def __init__(self, run_id, state=None, start_date=None, end_date=None, tests_all=None, tests_finished=None,
                 tests=None):
        self.run_id = run_id
        self.state = state
        self.start_date = start_date
        self.end_date = end_date
        self.tests_all = tests_all
        self.tests_finished = tests_finished
        self.tests = tests

    @classmethod
    def _from_api_response(cls, run_info):
        return cls(
            run_id=run_info["suiteId"],
            state=run_info.get("state"),
            start_date=run_info.get("startDate"),
            end_date=run_info.get("endDate"),
            tests_all=run_info.get("testsAll"),
            tests_finished=run_info.get("testsFinished"),
            tests=run_info.get("tests", [])
        )

    @classmethod
    def api_get_test_runs(cls, client=None):
        response = platform_tests.api_get_test_runs(client=client)
        test_runs = []
        for run_info in response:
            test = cls._from_api_response(run_info)
            test_runs.append(test)
        return test_runs

    @classmethod
    def api_get_test_run(cls, run_id, client=None):
        response = platform_tests.api_get_test_run(run_id, client=client)
        return cls._from_api_response(response)

    @classmethod
    def api_create(cls, username=None, password=None, client=None):
        if username is None:
            username = config.admin_username
        if password is None:
            password = config.admin_password
        response = platform_tests.api_create_test_run(username, password, client=client)
        run_id = response["suiteId"]
        time.sleep(3)
        tests = cls.api_get_test_runs()
        new_run = next((t for t in tests if t.run_id == run_id), None)
        assert new_run is not None, "No run returned with id {}".format(run_id)
        return new_run


class TestSuite:

    def __init__(self, id, title=None, approx_run_time=None, tests=None):
        self.id = id
        self.title = title
        self.approx_run_time = approx_run_time
        self.tests = tests

    @classmethod
    def _from_api_response(cls, suite_info):
        return cls(
            id=suite_info["id"],
            title=suite_info.get("title"),
            approx_run_time=suite_info.get("approxRunTime"),
            tests=suite_info.get("tests", [])
        )

    @classmethod
    def api_get_test_suites(cls, client=None):
        response = platform_tests.api_get_test_suites(client=client)
        test_suites = []
        for suite_info in response:
            suite = cls._from_api_response(suite_info)
            test_suites.append(suite)
        return test_suites
