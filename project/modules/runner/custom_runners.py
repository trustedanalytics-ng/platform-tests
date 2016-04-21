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
import unittest

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestResult, TeamcityTestRunner

from .. import tap_logger
from configuration import config
from ..constants import TestResult
from .db_client import DBClient
from .test_run_document import TestRunDocument
from .test_result_document import TestResultDocument


class _TextTestRunner(unittest.TextTestRunner):
    def __init__(self, stream=None, **kwargs):
        super(_TextTestRunner, self).__init__(stream=tap_logger.std_and_file_handler, **kwargs)


# select base class depending on whether tests are run on a TC agent or not
BaseResultClass = TeamcityTestResult if is_running_under_teamcity() else unittest.TextTestResult
BaseRunnerClass = TeamcityTestRunner if is_running_under_teamcity() else _TextTestRunner


class TapTestResult(BaseResultClass):

    @property
    def failed_test_ids(self):
        failed_tests = []
        for test, _ in self.errors + self.failures:
            if self.__is_error_holder(test):
                failed_tests.append(self.__test_name_from_error_holder(test.description))
            elif self.__is_subTest(test):
                failed_tests.append(test.test_case.full_name)
            elif self.__is_incremental(test):
                failed_tests.append(test.class_name)
            else:
                failed_tests.append(test.full_name)
        return list(set(failed_tests))

    @staticmethod
    def __test_name_from_error_holder(description):
        return re.split("\(|\)", description)[1]

    @staticmethod
    def __is_error_holder(obj):
        return obj.__class__.__name__ == "_ErrorHolder"

    @staticmethod
    def __is_subTest(obj):
        return obj.__class__.__name__ == "_SubTest"

    @staticmethod
    def __is_incremental(obj):
        return getattr(obj, "incremental", False)

    def addError(self, test, err):
        super().addError(test, err)
        self.__fail_incremental(test)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.__fail_incremental(test)

    @staticmethod
    def __fail_incremental(test):
        if getattr(test, "incremental", None) is not None:
            test.__class__.prerequisite_failed = True

    def stopTestRun(self):
        super().stopTestRun()
        failed_tests_file_path = config.CONFIG.get("failed_tests_file_path")
        if failed_tests_file_path is not None:
            with open(failed_tests_file_path, "w") as f:
                f.write("\n".join(self.failed_test_ids))


class TapTestRunner(BaseRunnerClass):
    resultclass = TapTestResult


class DBTestResult(TapTestResult):
    tests_to_run_count = None

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.__run = None
        self.__current_test = None
        self.__db_client = DBClient(uri=config.CONFIG["database_url"])
        self.__test_suite = config.CONFIG.get("test_suite")

    def startTestRun(self):
        super().startTestRun()
        self.__run = TestRunDocument(self.__db_client, environment=config.CONFIG["domain"], environment_version=None,
                                     suite=self.__test_suite, release=None, platform_components=[],
                                     tests_to_run_count=self.tests_to_run_count)
        self.__run.start()

    def stopTestRun(self):
        super().stopTestRun()
        self.__run.end()

    def startTest(self, test):
        super().startTest(test)
        self.__current_test = TestResultDocument(self.__db_client, run_id=self.__run.id, suite=self.__test_suite,
                                                 test_obj=test, test_order=self.testsRun, platform_components=[])
        self.__current_test.start()

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            result = TestResult.success
        else:
            result = TestResult.failure
            err = self._exc_info_to_string(err, test)
        self.__current_test.end_sub_test(subtest, result, error=err)
        self.__run.update_result(result=TestResult.success, sub_test_test=test)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.__current_test.end(result=TestResult.success)
        self.__run.update_result(result=TestResult.success)

    def addError(self, test, err):
        super().addError(test, err)
        if self.__current_test is not None:  # module setup / teardown failures
            self.__current_test.end(result=TestResult.error, error=self._exc_info_to_string(err, test))
            self.__run.update_result(result=TestResult.error)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.__current_test.end(result=TestResult.failure, error=self._exc_info_to_string(err, test))
        self.__run.update_result(result=TestResult.failure)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.__current_test.end(result=TestResult.skip, reason_skipped=reason)
        self.__run.update_result(result=TestResult.skip)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.__current_test.end(result=TestResult.expected_failure, error=self._exc_info_to_string(err, test))
        self.__run.update_result(result=TestResult.expected_failure)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.__current_test.end(result=TestResult.unexpected_success)
        self.__run.update_result(result=TestResult.unexpected_success)

    def run(self, test):
        return super().run(test)


class DBTestRunner(TapTestRunner):
    resultclass = DBTestResult

    def run(self, test):
        DBTestResult.tests_to_run_count = len(test._tests)
        super().run(test)
