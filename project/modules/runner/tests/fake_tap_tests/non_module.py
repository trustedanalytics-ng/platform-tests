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
import unittest

from modules.constants.priority_levels import Priority
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import incremental


def raise_error():
    x = []
    y = x[1]


class TearDownClassSwitchedOff(TapTestCase):
    @classmethod
    def tearDownClass(cls):
        pass


class PassingTestCase(TearDownClassSwitchedOff):

    def test_pass(self):
        self.assertTrue(True)


class FailingTestCase(TearDownClassSwitchedOff):

    def test_fail(self):
        self.assertTrue(False)

    def test_error(self):
        raise_error()


class PassAndFail(TearDownClassSwitchedOff):

    def test_pass(self):
        self.assertTrue(True)

    def test_fail(self):
        self.assertTrue(False)


class SetUpClassError(TearDownClassSwitchedOff):
    @classmethod
    def setUpClass(cls):
        raise_error()

    def test_pass(self):
        self.assertTrue(True)


class SetUpError(TearDownClassSwitchedOff):

    def setUp(self):
        raise_error()

    def test_pass(self):
        self.assertTrue(True)


class TearDownClassError(TapTestCase):

    @classmethod
    def tearDownClass(cls):
        raise_error()

    def test_pass(self):
        self.assertTrue(True)

    def test_fail(self):
        self.assertTrue(False)


class TearDownError(TearDownClassSwitchedOff):

    def tearDown(self):
        raise_error()

    def test_pass(self):
        self.assertTrue(True)

    def test_fail(self):
        self.assertTrue(False)


@incremental(Priority.medium)
class PassingIncremental(TearDownClassSwitchedOff):

    def test_0_pass(self):
        self.assertTrue(True)

    def test_1_pass(self):
        self.assertTrue(True)


@incremental(Priority.medium)
class FailingIncremental(TearDownClassSwitchedOff):

    def test_0_pass(self):
        self.assertTrue(True)

    def test_1_fail(self):
        self.assertTrue(False)

    def test_2_skip(self):
        self.assertTrue(True)


class FailingSubTest(TearDownClassSwitchedOff):

    def test_subtest(self):
        for v in [True, False, False, True]:
            with self.subTest(should_fail=(not v)):
                self.assertTrue(v)


class PassingSubTests(TearDownClassSwitchedOff):

    def test_subtest(self):
        for v in [True, True]:
            with self.subTest(should_fail=(not v)):
                self.assertTrue(v)


class MixedSubTestsAndFailTearDown(TearDownClassSwitchedOff):

    def tearDown(self):
        [][1]

    def test_subtest(self):
        for v in [True, False, False, True]:
            with self.subTest(should_fail=(not v)):
                self.assertTrue(v)


class ExpectedFailures(TearDownClassSwitchedOff):

    @unittest.expectedFailure
    def test_expected_failure_fails(self):
        self.assertTrue(False)

    @unittest.expectedFailure
    def test_unexpected_success(self):
        self.assertTrue(True)
