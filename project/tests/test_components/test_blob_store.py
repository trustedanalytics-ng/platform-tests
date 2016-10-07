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

import pytest

from modules.constants.urls import Urls
from modules.file_utils import download_file
from modules.tap_logger import step
from modules.tap_object_model.blob import Blob
from modules.constants import BlobStoreHttpStatus
from modules.markers import incremental
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestBlobStore:

    NODEJS_APP_NAME = "test_blob"

    @pytest.fixture(scope="class")
    def nodejs_app_path(self):
        return download_file(Urls.nodejs_app_url, self.NODEJS_APP_NAME)

    def test_0_create_artifact_in_blob_store(self, class_context, nodejs_app_path):
        step("Create artifact for an application in blob-store")
        self.__class__.test_blob = Blob.create(class_context, file_path=nodejs_app_path)
        step("Get the new blob from blob-store")
        blob = Blob.get(self.test_blob.id)
        assert blob == self.test_blob

    def test_1_cannot_create_artifact_in_blob_store_with_existing_id(self, class_context, nodejs_app_path):
        step("Creating artifact for application in blob-store with existing id should return an error")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_CONFLICT,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_ALREADY_IN_USE,
                                     Blob.create, class_context, self.test_blob.id,
                                     file_path=nodejs_app_path)

    def test_2_cannot_get_blob_with_non_existing_id(self):
        step("Getting non-existing blob should return an error")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get, "776a1f91-df7e-4032-4c31-7cd107719afb")

    def test_3_delete_blob(self):
        step("Delete blob from blob-store")
        self.test_blob.delete()
        step("Check that blob was successfully removed from blob-store")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get, self.test_blob.id)
