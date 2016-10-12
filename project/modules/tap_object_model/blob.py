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
    _COMPARABLE_ATTRIBUTES = ["id"]

    def __init__(self, *, blob_id: str):
        super().__init__(object_id=blob_id)

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, *, file_path, blob_id=None):
        if blob_id is None:
            blob_id = str(uuid.uuid4())
        blob_store_api.create_blob(blob_id=blob_id, file_path=file_path)
        new_blob = cls(blob_id=blob_id)
        context.blob_store.append(new_blob)
        return new_blob

    @classmethod
    def get(cls, *, blob_id: str):
        blob_store_api.get_blob(blob_id=blob_id)
        return cls(blob_id=blob_id)

    def delete(self):
        blob_store_api.delete_blob(blob_id=self.id)
