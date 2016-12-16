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

import uuid

import modules.http_calls.platform.blob_store as blob_store_api
from ._tap_object_superclass import TapObjectSuperclass


class Blob(TapObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["id", "content"]

    def __init__(self, *, blob_id: str, blob_content: bytes):
        super().__init__(object_id=blob_id)
        self.content = blob_content

    def __repr__(self):
        return "{} (id={}, size={})".format(self.__class__.__name__, self.id, len(self.content))

    @classmethod
    def create_from_file(cls, context, *, file_path, blob_id=None):
        if blob_id is None:
            blob_id = str(uuid.uuid4())
        blob_content = open(file_path, "rb").read()
        blob_store_api.create_blob_from_file(blob_id=blob_id, file_path=file_path)
        new_blob = cls(blob_id=blob_id, blob_content=blob_content)
        context.test_objects.append(new_blob)
        return new_blob

    @classmethod
    def create_from_data(cls, context, *, blob_content, blob_id=None):
        if blob_id is None:
            blob_id = str(uuid.uuid4())
        blob_store_api.create_blob_from_data(blob_id=blob_id, blob_content=blob_content)
        new_blob = cls(blob_id=blob_id, blob_content=blob_content)
        context.test_objects.append(new_blob)
        return new_blob

    @classmethod
    def try_create_blob_with_no_id(cls):
        """ Expected error: 'Bad request' """
        blob_store_api.create_blob_from_data(blob_id=None, blob_content=b"some-binary-data")

    @classmethod
    def try_create_blob_with_no_content(cls):
        """ Expected error: 'Bad request' """
        params = {"blobID": str(uuid.uuid4())}
        files = {"otherfile": b"some-binary-content"}
        blob_store_api.create_blob_raw_params(files=files, params=params)

    @classmethod
    def get(cls, *, blob_id: str):
        response = blob_store_api.get_blob(blob_id=blob_id)
        return cls(blob_id=blob_id, blob_content=response.content)

    @classmethod
    def delete_by_id(cls, *, blob_id):
        response = blob_store_api.delete_blob(blob_id=blob_id)
        return response

    def delete(self):
        return Blob.delete_by_id(blob_id=self.id)
