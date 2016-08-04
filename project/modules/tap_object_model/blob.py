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

import functools
import uuid

import config
import modules.http_calls.platform.blob_store as blob_store
from modules.constants.urls import Urls


@functools.total_ordering
class Blob(object):

    def __init__(self, blob_id: str, file_path: str):
        self.id = blob_id
        self.file_path = file_path

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, blob_id=None, file_path=None):
        if blob_id is None:
            blob_id = str(uuid.uuid4())
        if file_path is None:
            file_path = Urls.nodejs_app_url
        blob_store.create_blob(blob_id, file_path)
        new_blob = cls(blob_id, file_path)
        context.blob_store.append(new_blob)
        return new_blob

    @classmethod
    def get(cls, blob_id: str, api_version=config.ng_component_api_version):
        blob_store.get_blob(blob_id, api_version)
        return cls(blob_id, None)

    def delete(self):
        blob_store.delete_blob(self.id)

    def cleanup(self):
        self.delete()
