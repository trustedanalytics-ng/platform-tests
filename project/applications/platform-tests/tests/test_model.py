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

from unittest import mock

from bson.objectid import ObjectId
import mongomock
import pytest

from . import common
from app.model import TestSuiteModel, TestResultModel


mock_suite_collection = mongomock.MongoClient().db.collection
mock_test_collection = mongomock.MongoClient().db.collection


@pytest.mark.parametrize("document_params, expected_state",
                         [({}, "PASS"),
                          ({"status": "fail"}, "FAIL"),
                          ({"end_date": None}, "IN_PROGRESS"),
                          ({"interrupted": True}, "FAIL")])
def test_test_suite_model_init(document_params, expected_state):
    mock_document = common.get_example_run_document(**document_params)
    test_suite_model_dict = TestSuiteModel(mock_document).to_dict()
    assert test_suite_model_dict["suiteId"] == str(mock_document["_id"])
    assert test_suite_model_dict["startDate"] == mock_document["start_date"]
    assert test_suite_model_dict.get("endDate") == mock_document["end_date"]
    assert test_suite_model_dict["testsAll"] == mock_document["total_test_count"]
    assert test_suite_model_dict["testsFinished"] == mock_document["test_count"]
    assert test_suite_model_dict["state"] == expected_state


@mock.patch.object(TestSuiteModel, "_collection", mock_suite_collection)
def test_initialize_suite():
    suite_model = TestSuiteModel.initialize()
    assert isinstance(suite_model, TestSuiteModel)
    suite_list = TestSuiteModel.get_list()
    assert len(suite_list) == 1


@mock.patch.object(TestSuiteModel, "_collection", mock_suite_collection)
def test_get_list_one_suite(single_suite_document_id):
    suite_list = TestSuiteModel.get_list()
    assert len(suite_list) == 1
    assert single_suite_document_id == suite_list[0].id


@mock.patch.object(TestSuiteModel, "_collection", mock_suite_collection)
def test_get_list_multiple_suites(five_suite_document_ids):
    suite_list = TestSuiteModel.get_list()
    assert len(suite_list) == len(five_suite_document_ids)
    assert [s.id for s in suite_list] == five_suite_document_ids


@mock.patch.object(TestSuiteModel, "_collection", mock_suite_collection)
@mock.patch("app.model.TestResultModel._collection", mock_test_collection)
def test_get_suite_by_id(five_suite_document_ids):
    selected_id = five_suite_document_ids[3]
    suite_model = TestSuiteModel.get_by_id(suite_id=selected_id)
    assert isinstance(suite_model, TestSuiteModel)
    assert suite_model.id == selected_id


@mock.patch.object(TestSuiteModel, "_collection", mock_suite_collection)
def test_interrupted_suite(single_suite_document_id):
    suite_model = TestSuiteModel.get_list()[0]
    suite_model.set_interrupted()
    assert suite_model.is_interrupted()


@pytest.mark.parametrize("document_status", ["pass", "fail", "error", "skip"])
def test_test_result_init(document_status):
    mock_document = common.get_example_test_document(run_id=ObjectId(), status=document_status)
    test_model_dict = TestResultModel(mongo_document=mock_document).to_dict()
    assert test_model_dict["id"] == str(mock_document["_id"])
    assert test_model_dict["name"] == mock_document["name"]
    assert test_model_dict["order"] == mock_document["order"]
    assert test_model_dict["result"] == document_status.upper()
    assert test_model_dict["components"] == mock_document["components"]
    assert test_model_dict.get("stacktrace") == mock_document.get("stacktrace")


@mock.patch.object(TestResultModel, "_collection", mock_test_collection)
def test_test_result_by_suite_id():
    inserted_data = [
        {"suite_id": ObjectId(), "document_ids": []},
        {"suite_id": ObjectId(), "document_ids": []}
    ]
    for item in inserted_data:
        test_documents = [common.get_example_test_document(item["suite_id"]) for _ in range(5)]
        for test_doc in test_documents:
            mock_test_collection.insert_one(test_doc)
        item["document_ids"] = [str(t["_id"]) for t in test_documents]

    suite_id = inserted_data[0]["suite_id"]
    test_models = TestResultModel.get_list_by_suite_id(suite_id)
    test_model_ids = [model.to_dict()["id"] for model in test_models]
    assert test_model_ids == inserted_data[0]["document_ids"]


@pytest.fixture(scope="function")
def single_suite_document_id():
    run_document = common.get_example_run_document()
    return mock_suite_collection.insert_one(run_document).inserted_id


@pytest.fixture(scope="function")
def five_suite_document_ids():
    run_documents = [common.get_example_run_document() for _ in range(5)]
    return [mock_suite_collection.insert_one(run_doc).inserted_id for run_doc in run_documents]


@pytest.fixture(scope="function", autouse=True)
def cleanup_collections(request):
    def fin():
        mock_suite_collection.delete_many({})
        mock_test_collection.delete_many({})
    request.addfinalizer(fin)
