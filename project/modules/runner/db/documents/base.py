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


class BaseDocument(object):
    COLLECTION_NAME = None

    def __init__(self, db_client):
        self._id = None  # Primary key for a mongodb document.
        self._db_client = db_client

    @property
    def id(self):
        return self._id

    def _to_mongo_document(self):
        """Implentation in parent class."""

    def _insert(self):
        self._id = self._db_client.insert(
            collection_name=self.COLLECTION_NAME,
            document=self._to_mongo_document()
        )

    def _replace(self):
        self._db_client.replace(
            collection_name=self.COLLECTION_NAME,
            document_id=self._id,
            new_document=self._to_mongo_document()
        )

    def _upsert(self):
        if self._id is None:
            self._insert()
        else:
            self._replace()
