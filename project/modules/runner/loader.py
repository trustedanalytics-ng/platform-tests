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
import os
import unittest

from ..constants import Priority
from .decorators import MARK_DECORATOR_NAME
from .tap_test_case import TapTestCase


class EmptyTestSuiteException(Exception):
    def __init__(self):
        super().__init__("No tests found")


class TapTestLoader(unittest.TestLoader):
    ROOT_DIRECTORY = os.path.abspath(os.path.join("tests", "functional"))

    def __init__(self):
        self.__test_suite = self.discover(self.ROOT_DIRECTORY)
        self.__test_suite = self.flatten_test_suite(self.__test_suite)

    @property
    def test_suite(self):
        return self.__test_suite

    @property
    def tests(self):
        return self.__test_suite._tests

    @property
    def test_count(self):
        return len(self.__test_suite._tests)

    def load(self, path=None, test_name=None, priority=None, components=None, only_tags=None, excluded_tags=None):
        if path is not None:
            self.__filter_by_path(path=path)
        if test_name is not None:
            self.__filter_by_test_name(test_name=test_name)
        if components is not None and components != []:
            self.__filter_components(components)
        if priority is not None:
            self.__filter_priority(priority)
        if only_tags is not None and only_tags != []:
            self.__filter_only_tagged(only_tags)
        if excluded_tags is not None and excluded_tags != []:
            self.__filter_not_tagged(excluded_tags)
        return self.__test_suite

    def load_from_file(self, file_path):
        """Load tests from a test file containing a list of test class and test case names"""
        with open(file_path) as f:
            names = f.read().split("\n")

        def matches_name_or_class(test: TapTestCase):
            return test.class_name in names or test.full_name in names

        self.__filter_test_suite(matches_name_or_class)
        return self.__test_suite

    def __filter_by_path(self, path=None):
        path = "" if path is None else path
        load_path = os.path.join(self.ROOT_DIRECTORY, path)
        if os.path.isfile(load_path):
            start = path.replace(os.path.sep, ".").replace(".py", "")
        elif os.path.isdir(load_path):
            start = path.replace(os.path.sep, ".")
        else:
            raise NotADirectoryError("Directory {} doesn't exists".format(path))
        self.__filter_test_suite(lambda x: x.full_name.startswith(start))
        if self.__test_suite.countTestCases() == 0:
            raise EmptyTestSuiteException()

    def __filter_by_test_name(self, test_name):
        def matches_test_name(test: TapTestCase):
            return test_name in test.full_name
        self.__filter_test_suite(matches_test_name)

    @staticmethod
    def flatten_test_suite(test_suite: unittest.TestSuite):
        """
        Return unittest.TestSuite with flattened test list (i.e. not containing other TestSuites).
        """
        if not isinstance(test_suite, unittest.TestSuite):
            raise TypeError("not a TestSuite", test_suite)
        tests = []
        for item in test_suite._tests:
            if isinstance(item, unittest.TestSuite):
                tests.extend(TapTestLoader.flatten_test_suite(item))
            elif "ModuleImportFailure" in str(item):
                raise ImportError("Import failure in {}".format(item._testMethodName))
            else:
                tests.append(item)
        suite = unittest.TestSuite()
        suite.addTests(tests)
        return suite

    def __filter_test_suite(self, filter_method):
        """
        Return unittest.TestSuite formed of those tests from test_suite for which filter_method returns True.
        """
        tests = [t for t in self.__test_suite._tests if filter_method(t)]
        self.__test_suite._tests = tests

    def __filter_priority(self, priority: Priority):
        """Filters test cases with priority equal or higher to passed priority"""
        self.__filter_test_suite(lambda test: test.priority >= priority)

    def __filter_components(self, components: list):
        """Returns test cases marked with at least one of the passed components"""
        def has_component(test: TapTestCase):
            for component in test.components:
                if component in components:
                    return True
            return False
        self.__filter_test_suite(has_component)

    def __filter_only_tagged(self, tags: list):
        def is_tagged(test: TapTestCase):
            mark = getattr(test, MARK_DECORATOR_NAME, "")
            return mark in tags
        self.__filter_test_suite(is_tagged)

    def __filter_not_tagged(self, tags: list):
        def is_not_tagged(test: TapTestCase):
            mark = getattr(test, MARK_DECORATOR_NAME, "")
            return mark not in tags
        self.__filter_test_suite(is_not_tagged)
