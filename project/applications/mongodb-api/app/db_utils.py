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
from pymongo import MongoClient
from bson.objectid import ObjectId

from config import Config


class DatabaseClient(object):
    def __init__(self):
        c = Config()
        connection = MongoClient(c.db_hostname, port=c.db_port)
        self._database = connection[c.db_name]
        if c.db_username and c.db_password:
            self._database.authenticate(c.db_username, c.db_password)

    def get_collection_list(self):
        return self._database.collection_names()

    def add_collection(self, collection_name):
        self._database.create_collection(collection_name)

    def delete_collection(self, collection_name):
        self._database.drop_collection(collection_name)

    def get_documents(self, collection_name):
        result = self._database[collection_name].find({})
        return list(result)

    def add_document(self, collection_name, new_data):
        result = self._database[collection_name].insert_one(new_data)
        return str(result.inserted_id)

    def replace_document(self, collection_name, document_id, new_data):
        self._database[collection_name].replace_one({"_id": ObjectId(document_id)}, new_data)

    def delete_document(self, collection_name, document_id):
        self._database[collection_name].delete_one({"_id": ObjectId(document_id)})
