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
from pprint import pformat
from unittest.mock import patch
from unittest import TestCase, main

import mongomock

from modules.runner.custom_runners import DBTestRunner
from modules.runner.db.client import DBClient
from modules.runner.db.documents import TestResultDocument
from modules.tap_logger import get_logger

logger = get_logger(__name__)


class BaseDbTest(TestCase):

    TEST_FILE_PREFIX = "test_"

    def setUp(self):
        patcher = patch.object(DBClient, "__init__", autospec=True)
        _init = patcher.start()
        self.addCleanup(patcher.stop)

        self.db = mongomock.MongoClient().db

        def _init_(_self, uri):
            _self.database = self.db
        _init.side_effect = _init_

        self.test_class_name = self.__class__.__name__
        self.full_test_module_name = "modules.runner.tests.fake_tap_tests." \
                                     + self.__module__.split(".")[-1].replace(self.TEST_FILE_PREFIX, "", 1)

        self.__run_test()

    def __run_test(self):
        main(
            self.full_test_module_name,
            defaultTest=self.test_class_name,
            testRunner=DBTestRunner,
            argv=[""],
            exit=False
        )

    def _get_test_results(self):
        return list(self.db[TestResultDocument.COLLECTION_NAME].find())

    def _get_full_test_name(self, function_name, fixture):
        if fixture:
            name = [self.full_test_module_name]
            if isinstance(function_name, tuple):
                name.append(function_name[1])
                function_name = function_name[0]
            if "Module" not in function_name:
                name.insert(1, self.test_class_name)
            return "{} ({})".format(function_name, ".".join(name))
        else:
            return "{}.{}.{}".format(
                self.full_test_module_name,
                self.test_class_name,
                function_name
            )

    def assertResultDocuments(self, *args, count=-1):
        """
        :param args: status0, function_name0, is_fixture0, ...
            function_name can be a tuple, in such case there was error in setUp/tearDown (only),
                first element is an error function - a fixture method, and second the test name
        :param count: -1 same number as len(args)/3, None don't campare, else exact number
        """
        db_documents = self._get_test_results()
        logger.debug("Results: %s", pformat(db_documents))

        if count == -1:
            count = len(args)//3

        if count is not None:
            self.assertEqual(len(db_documents), count)

        it = iter(args)
        # change [
        #   status0, function_name0, is_fixture0,
        #   status1, function_name1, is_fixture1
        # ] into [
        #   (status0, function_name0, is_fixture0),
        #   (status1, function_name1, is_fixture1)
        # ]
        args_in_group_by_three = zip(it, it, it)

        db_name_and_status = [(i["name"], i["status"]) for i in db_documents]

        def create_name_and_status_from_one_group(args):
            return (
                self._get_full_test_name(args[1], args[2]),
                args[0].value
            )

        self.assertCountEqual(
            db_name_and_status,
            map(
                create_name_and_status_from_one_group,
                args_in_group_by_three
            )
        )
