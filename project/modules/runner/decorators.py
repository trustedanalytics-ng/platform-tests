#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License";
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

import functools
import inspect
import unittest

from ..constants import Priority


MARK_NAMES = ["long"]
MARK_DECORATOR_NAME = "mark"


class GenericDecorator(object):
    def __init__(self, value, decorator_name, possible_values):
        if value not in possible_values:
            raise TypeError("Only members {} are allowed".format(possible_values))
        self.decorator_value = value
        self.decorator_name = decorator_name

    def __call__(self, f):
        if not inspect.isfunction(f) or not f.__name__.startswith("test"):
            raise TypeError("{} decorator can only be used on a test method.".format(self.decorator_name))
        setattr(f, self.decorator_name, self.decorator_value)
        return f


class DecoratorGenerator(object):
    def __init__(self, possible_values, name):
        self.possible_values = possible_values
        self.name = name

    def __getattr__(self, item):
        if type(self.possible_values) != list:
            item = getattr(self.possible_values, item)
        return GenericDecorator(item, self.name, self.possible_values)


class ComponentDecorator(object):
    """For wrapping test classes and test methods. Specify a list of components tested by the class or method."""

    def __init__(self, *args):
        self.components = args

    def __call__(self, wrapped):
        wrapped.components = self.components
        return wrapped


class IncrementalTestDecorator(object):
    """
    For wrapping test classes which contain incremental tests.
    Tests will be run in alphabetical order. If there is an error or failure in a test, next ones will be skipped.
    Decorator takes an obligatory parameter of type Priority.
    """

    def __init__(self, priority):
        if not isinstance(priority, Priority):
            raise TypeError("Only members of Priority Enum are allowed")
        self.priority = priority

    def __call__(self, wrapped_class):
        if not inspect.isclass(wrapped_class):
            raise TypeError("Incremental decorator should be used on an ApiTestCase class.")
        self.wrapped_class = wrapped_class
        self.wrapped_class.incremental = True
        self.wrapped_class.prerequisite_failed = False
        self.__wrap_test_methods()
        return self.wrapped_class

    def __wrap_test_methods(self):
        test_method_names = [t for t in dir(self.wrapped_class) if t.startswith("test")]
        for test_method_name in test_method_names:
            test_method = getattr(self.wrapped_class, test_method_name)
            test_method.priority = self.priority
            wrapped_test_method = self.__test_method_wrapper(test_method)
            setattr(self.wrapped_class, test_method_name, wrapped_test_method)

    def __test_method_wrapper(self, func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            if self.wrapped_class.prerequisite_failed:
                raise unittest.SkipTest("Skipped due to failed prerequisite\n")
            func(*args, **kwargs)
        return wrap


priority = DecoratorGenerator(Priority, "priority")
components = ComponentDecorator
incremental = IncrementalTestDecorator
mark = DecoratorGenerator(MARK_NAMES, MARK_DECORATOR_NAME)
