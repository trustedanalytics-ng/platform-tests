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

from bson import ObjectId
from pymongo import MongoClient

from modules.tap_logger import get_logger

logger = get_logger(__name__)


class DBClient(object):

    def __init__(self, uri: str):
        """
        uri: mongodb://<host>:<port>/<dbname>
        """
        client = MongoClient(host=uri)
        database_name = uri.split("/")[-1]
        self.database = client[database_name]
        logger.debug("Connected to {} database on {}:{}".format(database_name, client.HOST, client.PORT))

    def insert(self, collection_name, document) -> ObjectId:
        result = self.database[collection_name].insert_one(document)
        logger.debug("Inserted document to {} with id {}".format(collection_name, result.inserted_id))
        return result.inserted_id

    def replace(self, collection_name: str, document_id: ObjectId, new_document: dict):
        data_filter = {"_id": document_id}
        self.database[collection_name].replace_one(data_filter, new_document)
        logger.debug("Updated document with id {}".format(collection_name, document_id))
