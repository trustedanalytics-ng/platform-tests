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

import time

from configuration import config
from modules.http_calls.platform import platform_tests


class TestSuite(object):

    IN_PROGRESS = "IN_PROGRESS"

    def __init__(self, suite_id, state=None, start_date=None, end_date=None, tests_all=None, tests_finished=None,
                 tests=None):
        self.suite_id = suite_id
        self.state = state
        self.start_date = start_date
        self.end_date = end_date
        self.tests_all = tests_all
        self.tests_finished = tests_finished
        self.tests = tests

    @classmethod
    def _from_api_response(cls, suite_info):
        return cls(
            suite_id=suite_info["suiteId"],
            state=suite_info.get("state"),
            start_date=suite_info.get("startDate"),
            end_date=suite_info.get("endDate"),
            tests_all=suite_info.get("testsAll"),
            tests_finished=suite_info.get("testsFinished"),
            tests=suite_info.get("tests", [])
        )

    @classmethod
    def api_get_list(cls, client=None):
        response = platform_tests.api_get_test_suites(client=client)
        test_suites = []
        for suite_info in response:
            test = cls._from_api_response(suite_info)
            test_suites.append(test)
        return test_suites

    @classmethod
    def api_get_test_suite_results(cls, suite_id, client=None):
        response = platform_tests.api_get_test_suite_results(suite_id, client=client)
        return cls._from_api_response(response)

    @classmethod
    def api_create(cls, username=None, password=None, client=None):
        if username is None:
            username = config.CONFIG["admin_username"]
        if password is None:
            password = config.CONFIG["admin_password"]
        response = platform_tests.api_create_test_suite(username, password, client=client)
        suite_id = response["suiteId"]
        time.sleep(3)
        tests = cls.api_get_list()
        new_suite = next((t for t in tests if t.suite_id == suite_id), None)
        assert new_suite is not None, "No suite returned with id {}".format(suite_id)
        return new_suite
