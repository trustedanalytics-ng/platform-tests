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

from modules.constants import Urls, TapComponent as TAP, BlobStoreHttpStatus
from modules.file_utils import download_file
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Blob
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.blob_store, )
pytestmark = [pytest.mark.components(TAP.blob_store)]


@pytest.mark.usefixtures("open_tunnel")
class TestBlobStore:

    non_existing_id = "776a1f91-df7e-4032-4c31-7cd107719afb"

    @pytest.fixture(scope="class")
    def nodejs_app_path(self):
        return download_file(Urls.nodejs_app_url, "test_blob")

    @pytest.fixture(scope="class")
    def sample_blob(self, class_context, nodejs_app_path):
        log_fixture("Create sample blob and check it exists")
        blob = Blob.create_from_file(class_context, file_path=nodejs_app_path)
        return Blob.get(blob_id=blob.id)

    @priority.high
    def test_create_and_delete_blob(self, context, nodejs_app_path):
        step("Create artifact in blob-store")
        test_blob = Blob.create_from_file(context, file_path=nodejs_app_path)

        step("Check that the blob exists")
        blob = Blob.get(blob_id=test_blob.id)
        assert blob == test_blob

        step("Delete the blob")
        test_blob.delete()

        step("Check that the blob was successfully removed from blob-store")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get, blob_id=test_blob.id)

    @priority.low
    def test_cannot_create_artifact_in_blob_store_with_existing_id(self, context, sample_blob, nodejs_app_path):
        step("Creating artifact for application in blob-store with existing id should return an error")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_CONFLICT,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_ALREADY_IN_USE,
                                     Blob.create_from_file, context, blob_id=sample_blob.id,
                                     file_path=nodejs_app_path)

    @priority.low
    def test_empty_blob(self, context):
        step("Create blob of size 0")
        stor_blob = Blob.create_from_data(context, blob_content=bytes())
        assert stor_blob.content == bytes()
        blob_id = stor_blob.id

        step("Retrieve blob of size 0")
        recv_blob = Blob.get(blob_id=blob_id)
        assert stor_blob == recv_blob

        step("Delete blob of size 0")
        Blob.delete_by_id(blob_id=blob_id)

        step("Check that blob of size 0 was successfully removed from blob-store")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get,
                                     blob_id=blob_id)

    @priority.medium
    def test_operations_on_one_blob_do_not_affect_others(self, context):
        NUM_BLOBS = 5
        BLOB_CONTENTS = [bytes("test_blob_content_{0}".format(i), "utf-8") for i in range(NUM_BLOBS)]

        stored_blobs = []
        for i, content in enumerate(BLOB_CONTENTS):
            step("Multiple blobs: create blob '{}'".format(i))
            blob = Blob.create_from_data(context, blob_content=content)
            assert blob.content == content
            stored_blobs.append(blob)
        for stor_blob, content in zip(stored_blobs, BLOB_CONTENTS):
            blob_id = stor_blob.id
            step("Multiple blobs: check content of blob '{}'".format(blob_id))
            recv_blob = Blob.get(blob_id=blob_id)
            assert recv_blob == stor_blob
            step("Multiple blobs: delete blob '{}'".format(blob_id))
            Blob.delete_by_id(blob_id=blob_id)
            step("Multiple blobs: check blob '{}' deleted".format(blob_id))
            assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                         BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                         Blob.get, blob_id=blob_id)

    @priority.low
    def test_cannot_create_blob_if_blob_id_is_empty(self, context):
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_BAD_REQUEST,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_MISSING,
                                     Blob.create_from_data,
                                     context, blob_id="", blob_content=b'anything')

    @priority.low
    def test_cannot_create_blob_if_blob_id_is_missing(self):
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_BAD_REQUEST,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_MISSING,
                                     Blob.try_create_blob_with_no_id)

    @priority.low
    def test_cannot_create_blob_if_uploadfile_is_missing(self):
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_BAD_REQUEST,
                                     BlobStoreHttpStatus.MSG_BLOB_CONTENT_MISSING,
                                     Blob.try_create_blob_with_no_content)

    @priority.low
    def test_cannot_retrieve_nonexistent_blob(self):
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get,
                                     blob_id=self.non_existing_id)

    @priority.low
    def test_cannot_delete_nonexistent_blob(self):
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.delete_by_id,
                                     blob_id=self.non_existing_id)
