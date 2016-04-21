#
# Copyright (c) 2015-2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import functools
import time
import unittest

from retry import retry

from ..constants import LoggerType, Priority
from ..exceptions import UnexpectedResponseError
from ..tap_logger import get_logger
from ..tap_object_model import organization, user, transfer, dataset


logger = get_logger(__name__)


FUNCTIONS_TO_LOG = ('setUp', 'tearDown', 'setUpClass', 'tearDownClass')
SEPARATOR = "****************************** {} {} {} ******************************"


def log_fixture_separator(func):
    func_is_classmethod = type(func) is classmethod
    if func_is_classmethod:
        func = func.__func__
    func_name = func.__name__

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        class_name = "in {}".format(args[0].__name__) if func_is_classmethod else ""
        logger.debug(SEPARATOR.format("BEGIN", func_name, class_name))
        func(*args, **kwargs)
        logger.debug(SEPARATOR.format("END", func_name, class_name))

    if func_is_classmethod:
        return classmethod(wrapper)
    else:
        return wrapper


class SeparatorMeta(type):
    def __new__(mcs, name, bases, namespace):
        for attr, obj in namespace.items():
            if attr in FUNCTIONS_TO_LOG:
                namespace[attr] = log_fixture_separator(obj)
        return super(SeparatorMeta, mcs).__new__(mcs, name, bases, namespace)


class TapTestCase(unittest.TestCase, metaclass=SeparatorMeta):
    step_number = 0
    sub_test_number = 0
    incremental = False

    maxDiff = None
    components = tuple()

    def __init__(self, methodName="runTest"):
        test_method = getattr(self.__class__, methodName)
        priority = getattr(test_method, "priority", None)
        super().__init__(methodName=methodName)
        self.priority = Priority.default() if priority is None else priority
        self.components = getattr(test_method, "components", self.components)
        self.mark = getattr(test_method, "mark", None)
        self.class_name = "{}.{}".format(self.__class__.__module__, self.__class__.__name__)
        self.full_name = "{}.{}".format(self.class_name, self._testMethodName)

    @classmethod
    def tearDownClass(cls):
        dataset.DataSet.api_teardown_test_datasets()
        transfer.Transfer.api_teardown_test_transfers()
        organization.Organization.cf_api_tear_down_test_orgs()
        user.User.cf_api_tear_down_test_users()
        user.User.api_tear_down_test_invitations()

    @classmethod
    def get_errors_and_failures(cls, result):
        return len(result.errors) + len(result.failures)

    @classmethod
    def step(cls, message):
        """Log message as nth test step"""
        separator = "=" * 20
        step_logger = get_logger(LoggerType.STEP_LOGGER)
        step_logger.info("{0} Step {1} {2} {0}".format(separator, cls.step_number, message))
        cls.step_number += 1

    def subTest(self, msg=None, **params):
        separator = "*" * 20
        logged_params = ",".join(["{}={}".format(k, v) for k, v in params.items()])
        logger.info("{0} Sub test {1} ({2})".format(separator, self.sub_test_number, logged_params))
        sub_test_returns = super().subTest(msg, **params)
        self.__class__.step_number = 0
        self.__class__.sub_test_number += 1
        return sub_test_returns

    def run(self, result=None):
        test_name = "{}.{}".format(self.__class__.__name__, self._testMethodName)
        separator = "*" * len(test_name)
        self.__class__.step_number = self.__class__.sub_test_number = 0
        logger.debug("\n{0}\n\n{1}\n\n{0}\n".format(separator, test_name))
        return super().run(result=result)

    def assertUnorderedListEqual(self, list1, list2, msg=None):
        self.assertListEqual(sorted(list1), sorted(list2), msg=msg)

    def assertRaisesUnexpectedResponse(self, status, error_message_phrase, callableObj, *args, **kwargs):
        """error_message_phrase - a phrase which should be a part of error message"""
        with self.assertRaises(UnexpectedResponseError) as e:
            callableObj(*args, **kwargs)
        status_correct = e.exception.status == status
        if error_message_phrase == "":
            error_message_contains_string = error_message_phrase == ""
        else:
            error_message_contains_string = error_message_phrase in e.exception.error_message
        self.assertTrue(status_correct and error_message_contains_string,
                        "Error is {0} \"{1}\", expected {2} \"{3}\"".format(e.exception.status,
                                                                            e.exception.error_message,
                                                                            status, error_message_phrase))

    def assertReturnsError(self, callableObj, *args, **kwargs):
        """Assert that response error code is 4XX or 5XX"""
        with self.assertRaises(UnexpectedResponseError) as e:
            callableObj(*args, **kwargs)
        status_first_digit = e.exception.status // 100
        self.assertIn(status_first_digit, (4, 5), "Status code: {}. Expected: 4XX or 5XX".format(e.exception.status))

    def assertEqualWithinTimeout(self, timeout, expected_result, callable_obj, *args, **kwargs):
        now = time.time()
        while time.time() - now < timeout:
            result = callable_obj(*args, **kwargs)
            if result == expected_result:
                return
            time.sleep(5)
        self.fail("{} and {} are not equal - within {}s".format(result, expected_result, timeout))

    def assert_user_in_org_and_roles(self, invited_user, org_guid, expected_roles):
        self.step("Check that the user is in the organization with expected roles ({}).".format(expected_roles))
        org_users = user.User.api_get_list_via_organization(org_guid)
        self.assertIn(invited_user, org_users, "Invited user is not on org users list")
        invited_user_roles = list(invited_user.org_roles.get(org_guid, []))
        self.assertUnorderedListEqual(invited_user_roles, list(expected_roles),
                                      "User's roles in org: {}, expected {}".format(invited_user_roles,
                                                                                    list(expected_roles)))

    @retry(AssertionError, tries=10, delay=2)
    def assertNotInWithRetry(self, something, get_list_method, *args, **kwargs):
        """Use when deleting something takes longer"""
        obj_list = get_list_method(*args, **kwargs)
        self.assertNotIn(something, obj_list)

    @retry(AssertionError, tries=10, delay=2)
    def assertInWithRetry(self, something, get_list_method, *args, **kwargs):
        """Use when adding something takes longer"""
        obj_list = get_list_method(*args, **kwargs)
        self.assertIn(something, obj_list)

    @retry(AssertionError, tries=60, delay=2)
    def get_from_list_by_attribute_with_retry(self, attr_name, attr_value, get_list_method, *args, **kwargs):
        """Get list repeatedly and return item with particular attribute value"""
        items = get_list_method(*args, **kwargs)
        thing = next((i for i in items if getattr(i, attr_name) == attr_value), None)
        self.assertIsNotNone(thing)
        return thing


def cleanup_after_failed_setup(*cleanup_methods):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                for cleanup_method in cleanup_methods:
                    cleanup_method()
                raise
        return wrapped
    return wrapper


