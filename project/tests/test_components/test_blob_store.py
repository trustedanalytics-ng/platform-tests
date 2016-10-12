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
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Blob
from modules.constants import BlobStoreHttpStatus
from tests.fixtures.assertions import assert_raises_http_exception


@pytest.mark.usefixtures("open_tunnel")
class TestBlobStore:

    @pytest.fixture(scope="class")
    def nodejs_app_path(self):
        return download_file(Urls.nodejs_app_url, "test_blob")

    @pytest.fixture(scope="class")
    def sample_blob(self, class_context, nodejs_app_path):
        log_fixture("Create sample blob and check it exists")
        blob = Blob.create(class_context, file_path=nodejs_app_path)
        return Blob.get(blob_id=blob.id)

    def test_create_and_delete_blob(self, context, nodejs_app_path):
        step("Create artifact in blob-store")
        test_blob = Blob.create(context, file_path=nodejs_app_path)

        step("Check that the blob exists")
        blob = Blob.get(blob_id=test_blob.id)
        assert blob == test_blob

        step("Delete the blob")
        test_blob.delete()

        step("Check that the blob was successfully removed from blob-store")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get, blob_id=test_blob.id)

    def test_cannot_create_artifact_in_blob_store_with_existing_id(self, context, sample_blob, nodejs_app_path):
        step("Creating artifact for application in blob-store with existing id should return an error")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_CONFLICT,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_ALREADY_IN_USE,
                                     Blob.create, context, blob_id=sample_blob.id,
                                     file_path=nodejs_app_path)

    def test_cannot_get_blob_with_non_existing_id(self):
        step("Getting non-existing blob should return an error")
        non_existing_id = "776a1f91-df7e-4032-4c31-7cd107719afb"
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get, blob_id=non_existing_id)


