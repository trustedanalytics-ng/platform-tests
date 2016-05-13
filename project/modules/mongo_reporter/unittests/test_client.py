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

from bson import ObjectId
import mongomock

from modules.mongo_reporter import client


@mock.patch.object(client, "MongoClient", mongomock.MongoClient)
class TestMongoClient:
    test_document = {"hello": "kitty", "int": 1, "bool": True, "none": None}
    test_db_name = "test_db"
    test_collection_name = "test_collection"
    uri = "mongodb://mockmongo:1234/{}".format(test_db_name)

    def test_init(self):
        db_client = client.DBClient(uri=self.uri)
        assert db_client.database.name == self.test_db_name

    def test_insert(self):
        db_client = client.DBClient(uri=self.uri)
        test_document = self.test_document.copy()
        document_id = db_client.insert(collection_name=self.test_collection_name, document=test_document)
        assert isinstance(document_id, ObjectId)
        documents = list(db_client.database[self.test_collection_name].find({}))
        assert len(documents) == 1
        test_document.update({"_id": document_id})
        assert test_document == documents[0]

    def test_replace(self):
        db_client = client.DBClient(uri=self.uri)
        test_document = self.test_document.copy()
        document_id = db_client.insert(collection_name=self.test_collection_name, document=test_document)
        test_document.update({"new": "field", "bool": False})
        db_client.replace(collection_name=self.test_collection_name, document_id=document_id, new_document=test_document)
        documents = list(db_client.database[self.test_collection_name].find({}))
        assert len(documents) == 1
        test_document.update({"_id": document_id})
        assert test_document == documents[0]




