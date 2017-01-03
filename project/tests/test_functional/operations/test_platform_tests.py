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
from modules.tap_object_model import TestRun

logged_components = (TAP.platform_tests,)
pytestmark = [pytest.mark.components(TAP.platform_tests)]


@incremental
@priority.high
class TestSelfTests:

    def test_1_start_self_tests_or_get_one_in_progress(self):
        """
        <b>Description:</b>
        Tries to create new test run if no test run is running.
        If some test runs are running its status is checked.

        <b>Input data:</b>
        no input data

        <b>Expected results:</b>
        New test run is created, it's status is running.

        <b>Steps:</b>
        1. Create new test run.
        2. Verify that its status is running.
        3. If other run is in progress inform user, and check does tests running in tests runs exist.
        """
        step("Start tests")
        try:
            new_test = TestRun.api_create()
            step("New test suite has been started")
            self.__class__.run_id = new_test.run_id
            assert new_test.state == TestRun.IN_PROGRESS, "New test run state is {}".format(new_test.state)
        except UnexpectedResponseError as e:
            step("Another run is already in progress")
            assert e.status == PlatformTestsHttpStatus.CODE_TOO_MANY_REQUESTS
            assert PlatformTestsHttpStatus.MSG_RUNNER_BUSY in e.error_message
            step("Get list of test runs and retrieve run in progress")
            tests = TestRun.api_get_test_runs()
            test_in_progress = next((t for t in tests if t.state == TestRun.IN_PROGRESS), None)
            assert test_in_progress is not None, "Cannot create test run, although no other run is in progress"
            self.__class__.run_id = test_in_progress.run_id

    def test_2_get_test_run_details(self):
        """
        <b>Description:</b>
        Gets test run details.

        <b>Input data:</b>
        no input data

        <b>Expected results:</b>
        Verifies that results created by test run are not None.

        <b>Steps:</b>
        1. Get results of test run.
        2. Verify that results are not None.
        """
        step("Get test run details")
        created_test_results = TestRun.api_get_test_run(self.run_id)
        assert created_test_results is not None
