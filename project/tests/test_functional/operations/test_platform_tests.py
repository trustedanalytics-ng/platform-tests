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
import pytest

from modules.constants import TapComponent as TAP
from modules.constants.http_status import PlatformTestsHttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import TestSuite

logged_components = (TAP.platform_tests,)
pytestmark = [pytest.mark.components(TAP.platform_tests)]


@incremental
@priority.high
class TestSelfTests:

    def test_1_start_self_tests_or_get_suite_in_progress(self):
        step("Start tests")
        try:
            new_test = TestSuite.api_create()
            step("New test suite has been started")
            self.__class__.suite_id = new_test.suite_id
            assert new_test.state == TestSuite.IN_PROGRESS, "New suite state is {}".format(new_test.state)
        except UnexpectedResponseError as e:
            step("Another suite is already in progress")
            assert e.status == PlatformTestsHttpStatus.CODE_TOO_MANY_REQUESTS
            assert PlatformTestsHttpStatus.MSG_RUNNER_BUSY in e.error_message
            step("Get list of test suites and retrieve suite in progress")
            tests = TestSuite.api_get_list()
            test_in_progress = next((t for t in tests if t.state == TestSuite.IN_PROGRESS), None)
            assert test_in_progress is not None, "Cannot create suite, although no other suite is in progress"
            self.__class__.suite_id = test_in_progress.suite_id

    def test_2_get_suite_details(self):
        step("Get suite details")
        created_test_results = TestSuite.api_get_test_suite_results(self.suite_id)
        assert created_test_results is not None
