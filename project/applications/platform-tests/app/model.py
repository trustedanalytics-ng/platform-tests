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

from bson.objectid import ObjectId
import pymongo

from .config import DatabaseConfig
from .suite_provider import SuiteProvider


class DatabaseClient(object):
    __config = DatabaseConfig()
    __client = pymongo.MongoClient(__config.uri)
    __database = __client[__config.dbname]

    suite_collection = __database[__config.test_suite_collection]
    test_result_collection = __database[__config.test_result_collection]


class TestResultModel(object):
    _collection = DatabaseClient.test_result_collection

    def __init__(self, mongo_document: dict):
        """Initialize based on mongo_document dict representation."""
        self.__id = mongo_document["_id"]
        self.__name = mongo_document.get("name")
        self.__order = mongo_document.get("order")
        self.__result = mongo_document.get("status")
        if self.__result is not None:
            self.__result = self.__result.upper()
        self.__components = mongo_document.get("components")
        self.__stacktrace = mongo_document.get("stacktrace")

    @classmethod
    def get_list_by_suite_id(cls, suite_id: ObjectId):
        results = cls._collection.find({"run_id": suite_id})
        test_results = []
        for test_result_document in results:
            test_results.append(cls(mongo_document=test_result_document))
        return test_results

    def to_dict(self):
        result = {
            "id": str(self.__id),
            "name": self.__name,
            "order": self.__order,
            "result": self.__result,
            "components": self.__components,
            "stacktrace": self.__stacktrace
        }
        result = {x: y for x, y in result.items() if y is not None}
        return result


class TestSuiteModel(object):
    _collection = DatabaseClient.suite_collection
    INTERRUPTED_KEY = "interrupted"

    def __init__(self, mongo_document: dict, test_results: list=None):
        """Initialize based on mongo_document dict representation."""
        self.__id = mongo_document["_id"]
        self.__start_date = mongo_document.get("start_date")
        self.__end_date = mongo_document.get("end_date")
        self.__state = self.__determine_state(mongo_document)
        self.__tests_all = mongo_document.get("total_test_count")
        self.__tests_finished = mongo_document.get("test_count")
        self.__test_results = test_results

    @property
    def id(self):
        return self.__id

    @staticmethod
    def __determine_state(mongo_document):
        state = mongo_document.get("status")
        if mongo_document.get("interrupted"):
            suite_state = "FAIL"
        elif state is None:
            suite_state = None
        elif mongo_document.get("end_date") is None:
            suite_state = "IN_PROGRESS"
        else:
            suite_state = state.upper()
        return suite_state

    @staticmethod
    def _get_filter(suite_id: ObjectId):
        return {"_id": suite_id}

    @classmethod
    def initialize(cls):
        """
        Insert new, empty document into suite collection.
        Return TestSuiteModel with newly-inserted object id.
        """
        suite_id = cls._collection.insert_one({}).inserted_id
        return cls(mongo_document={"_id": suite_id})

    def is_interrupted(self):
        """
        Query database. Return True if the test suite has interrupted flag set.
        """
        suite_document = self._collection.find_one(self._get_filter(self.id))
        return suite_document.get(self.INTERRUPTED_KEY) is True

    def set_interrupted(self):
        """
        Update test suite mongodb document, setting interrupted flag.
        """
        update_field = {"$set": {self.INTERRUPTED_KEY: True}}
        self._collection.update_one(self._get_filter(self.id), update=update_field)

    @classmethod
    def get_by_id(cls, suite_id: ObjectId):
        """
        Query database and return suite with given suite_id together with detailed test results.
        """
        suite = cls._collection.find_one(cls._get_filter(suite_id))
        test_results = TestResultModel.get_list_by_suite_id(suite_id)
        return cls(mongo_document=suite, test_results=test_results)

    @classmethod
    def get_list(cls):
        """
        Query database and return all suites.
        """
        suite_documents = cls._collection.find()
        suites = []
        for suite_document in suite_documents:
            suites.append(cls(mongo_document=suite_document))
        return suites

    @classmethod
    def get_last_five(cls):
        """
        Query database and return last five runs.
        """
        return cls._collection.find({'end_date': {'$ne': None}}, sort=[("end_date", pymongo.DESCENDING)]).limit(5)

    def to_dict(self):
        result = {
            "suiteId": str(self.id),
            "state": self.__state,
            "startDate": str(self.__start_date),
            "endDate": str(self.__end_date),
            "testsAll": self.__tests_all,
            "testsFinished": self.__tests_finished,
            "testName": SuiteProvider.SUITE_NAME
        }
        if self.__test_results is not None:
            result["tests"] = [t.to_dict() for t in self.__test_results]
        result = {x: y for x, y in result.items() if y is not None}
        return result
