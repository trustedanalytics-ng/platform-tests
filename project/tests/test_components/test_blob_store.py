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

from modules.constants import TapComponent as TAP, BlobStoreHttpStatus
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
    def sample_blob(self, class_context, test_data_urls):
        log_fixture("Create sample blob and check it exists")
        blob = Blob.create_from_file(class_context, file_path=test_data_urls.nodejs_app.filepath)
        return Blob.get(blob_id=blob.id)

    @priority.high
    def test_create_and_delete_blob(self, context, test_data_urls):
        """
        <b>Description:</b>
        Create and delete blob from blob store

        <b>Input data:</b>
        nodejs application that will be used to create the blob

        <b>Expected results:</b>
        - It's possible to create the blob
        - It's possible to delete the blob

        <b>Steps:</b>
        - Create blob and push it
        - Verify the blob can be retrieved by id
        - Delete the blob
        - Verify that the blob is no longer in blob store
        """
        step("Create artifact in blob-store")
        test_blob = Blob.create_from_file(context, file_path=test_data_urls.nodejs_app.filepath)

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
    def test_cannot_create_artifact_in_blob_store_with_existing_id(self, context, sample_blob, test_data_urls):
        """
        <b>Description:</b>
        Attempt to create blob with duplicated id

        <b>Input data:</b>
        - nodejs application turned to blob
        - id of the blob

        <b>Expected results:</b>
        It's not possible to create another blob with the same id

        <b>Steps:</b>
        - Push blob
        - Push another blob with the id same one as previous blob
        """
        step("Creating artifact for application in blob-store with existing id should return an error")
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_CONFLICT,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_ALREADY_IN_USE,
                                     Blob.create_from_file, context, blob_id=sample_blob.id,
                                     file_path=test_data_urls.nodejs_app.filepath)

    @priority.low
    def test_empty_blob(self, context):
        """
        <b>Description:</b>
        Try pushing an empty blob

        <b>Input data:</b>
        Empty blob

        <b>Expected results:</b>
        It's possible to push and remove later an empty blob

        <b>Steps:</b>
        - Create a blob of 0 size
        - Push the blob and verify it's presence on platform
        - Remove the blob and verify it's no longer present
        """
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
        """
        <b>Description:</b>
        Verify that working on one blob doesn't affect other blobs

        <b>Input data:</b>
        Multiple blobs

        <b>Expected results:</b>
        Blobs remain intact

        <b>Steps:</b>
        - Push multiple blobs and verify their contents
        - Remove the blobs and verify they were removed
        """
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
        """
        <b>Description:</b>
        Try pushing blob with empty id

        <b>Input data:</b>
        Blob with empty id

        <b>Expected results:</b>
        It's not possible to push blob with empty id

        <b>Steps:</b>
        - Push blob but do not provide any id
        - Verify that platform returns error
        """
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_BAD_REQUEST,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_MISSING,
                                     Blob.create_from_data,
                                     context, blob_id="", blob_content=b'anything')

    @priority.low
    def test_cannot_create_blob_if_blob_id_is_missing(self):
        """
        <b>Description:</b>
        Try pushing blob with id field remove

        <b>Input data:</b>
        Blob that has no id field

        <b>Expected results:</b>
        It's not possible to push blob with no id field

        <b>Steps:</b>
        - Push blob with no id field
        - Verify that platform returned error
        """
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_BAD_REQUEST,
                                     BlobStoreHttpStatus.MSG_BLOB_ID_MISSING,
                                     Blob.try_create_blob_with_no_id)

    @priority.low
    def test_cannot_create_blob_if_uploadfile_is_missing(self):
        """
        <b>Description:</b>
        Try pushing blob with no uploadfile

        <b>Input data:</b>
        Blob with missing uploadfile

        <b>Expected results:</b>
        It's not possible to push blob with missing uploadfile

        <b>Steps:</b>
        - Push blob with missing uploadfile
        - Verify that platform returned error
        """
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_BAD_REQUEST,
                                     BlobStoreHttpStatus.MSG_BLOB_CONTENT_MISSING,
                                     Blob.try_create_blob_with_no_content)

    @priority.low
    def test_cannot_retrieve_nonexistent_blob(self):
        """
        <b>Description:</b>
        Try to retrieve non-existent blob

        <b>Input data:</b>
        Made up id

        <b>Expected results:</b>
        It's not possible to retrieve blob with non-existent id

        <b>Steps:</b>
        - Ask for id that does not exist
        - Verify platform returned error
        """
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get,
                                     blob_id=self.non_existing_id)

    @priority.low
    def test_cannot_delete_nonexistent_blob(self):
        """
        <b>Description:</b>
        Try

        <b>Input data:</b>
        Made up id

        <b>Expected results:</b>
        It's not possible to delete id that does not exist

        <b>Steps:</b>
        - Delete blob that has wrong id
        - Verify the platform returned error
        """
        assert_raises_http_exception(BlobStoreHttpStatus.CODE_NOT_FOUND,
                                     BlobStoreHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.delete_by_id,
                                     blob_id=self.non_existing_id)
