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

from datetime import datetime
import socket

from bson.objectid import ObjectId

from modules.runner.db.documents.base import BaseDocument
from modules.runner.db.client import DBClient
from modules.constants import TestResult
from modules.platform_version import VersionedComponent
from configuration.config import CONFIG


class TestRunDocument(BaseDocument):
    COLLECTION_NAME = "test_run"
    sub_test_tests = []

    def __init__(self, db_client: DBClient, environment, environment_version, suite, release, platform_components,
                 tests_to_run_count):
        super().__init__(db_client)
        self.__environment = environment
        self.__environment_version = environment_version
        self.__suite = suite
        self.__release = release
        self.__platform_components = platform_components
        self.__tests_to_run_count = tests_to_run_count

        self.__started_by = socket.gethostname()

        self.__id = None
        self.__start_date = None
        self.__end_date = None
        self.__status = TestResult.success
        self.__test_count = 0
        self.__result = {v: 0 for v in TestResult.values()}
        self.log = None

    def update_result(self, result: TestResult, sub_test_test=None):
        if sub_test_test is not None and sub_test_test not in self.sub_test_tests:
            self.sub_test_tests.append(sub_test_test)
            self.__test_count += 1
        self.__test_count += 1
        self.__result[result.value] += 1
        if result not in (TestResult.success, TestResult.expected_failure):
            self.__status = TestResult.failure
        self._replace()

    def start(self):
        self.__start_date = datetime.now().isoformat()
        run_id = CONFIG.get("test_run_id")
        if run_id is not None:
            self.__id = ObjectId(run_id)
            self._replace()
        else:
            self._insert()

    def end(self):
        self.__end_date = datetime.now().isoformat()
        self._replace()

    def _to_mongo_document(self):
        return {
            "environment": self.__environment,
            "environment_version": self.__environment_version,
            "suite": self.__suite,
            "started_by": self.__started_by,
            "release": self.__release,
            "platform_components": VersionedComponent.list_to_db_format(self.__platform_components),
            "start_date": self.__start_date,
            "end_date": self.__end_date,
            "test_count": self.__test_count,
            "total_test_count": self.__tests_to_run_count,
            "result": self.__result,
            "status": self.__status.value,
            "log": self.log
        }
