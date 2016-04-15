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

from modules.runner.db.documents.base import BaseDocument
from modules.runner.db.client import DBClient
from modules.constants import TestResult


class FixtureDocument(BaseDocument):
    """During error in setUp/tearDown/setUpClass/tearDownClass/setUpModule/tearDownModule."""

    COLLECTION_NAME = "test_result"

    def __init__(self, db_client: DBClient, run_id: str, suite: str, name: str, stacktrace: str):
        super().__init__(db_client)
        self.__run_id = run_id
        self.__suite = suite
        self.__name = name

        self.__id = None
        self.__result = TestResult.error
        self.__reason_skipped = None
        self.__stacktrace = stacktrace
        self.log = None

    def insert(self):
        self._insert()

    def _to_mongo_document(self):
        return {
            "run_id": self.__run_id,
            "suite": self.__suite,
            "name": self.__name,
            "status": self.__result.value,
            "reason_skipped": self.__reason_skipped,
            "stacktrace": self.__stacktrace,
            "log": self.log,
        }
