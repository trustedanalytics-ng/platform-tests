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
from modules.runner.tests.db_tests.base_test import BaseDbTest
from modules.constants.test_results import TestResult


class PassingTestCase(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_pass", False
        )


class FailingTestCase(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.failure, "test_fail", False,
            TestResult.error, "test_error", False
        )


class PassAndFail(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_pass", False,
            TestResult.failure, "test_fail", False
        )


class SetUpClassError(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.error, "setUpClass", True
        )


class SetUpError(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.error, ("setUp", "test_pass"), True
        )


class TearDownClassError(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_pass", False,
            TestResult.failure, "test_fail", False,
            TestResult.error, "tearDownClass", True
        )


class TearDownError(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_pass", False,
            TestResult.error, ("tearDown", "test_pass"), True,
            TestResult.failure, "test_fail", False,
            TestResult.error, ("tearDown", "test_fail"), True
        )


class PassingIncremental(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_0_pass", False,
            TestResult.success, "test_1_pass", False
        )


class FailingIncremental(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_0_pass", False,
            TestResult.failure, "test_1_fail", False,
            TestResult.skip, "test_2_skip", False
        )


class FailingSubTest(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.failure, "test_subtest", False
        )


class PassingSubTests(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_subtest", False
        )


class MixedSubTestsAndFailTearDown(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.failure, "test_subtest", False,
            TestResult.error, ("tearDown", "test_subtest"), True
        )


class ExpectedFailures(BaseDbTest):
    def test_documents(self):
        self.assertResultDocuments(
            TestResult.expected_failure, "test_expected_failure_fails", False,
            TestResult.unexpected_success, "test_unexpected_success", False
        )
