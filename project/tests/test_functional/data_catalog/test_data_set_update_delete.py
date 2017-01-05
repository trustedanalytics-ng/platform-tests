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
from retry import retry

from modules.constants import HttpStatus, TapComponent as TAP, Urls
from modules.exceptions import UnexpectedResponseError
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet
from modules.tap_object_model.flows import data_catalog

logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


class TestUpdateDeleteDataSet:
    TEST_FILE_URL = Urls.test_transfer_link

    @retry(AssertionError, tries=10, delay=3)
    def _assert_updated(self, data_set_id, updated_attribute_name, expected_value):
        updated_dataset = DataSet.api_get(data_set_id)
        updated_value = getattr(updated_dataset, updated_attribute_name)
        assert updated_value == expected_value, "Data set was not updated"

    @pytest.fixture(scope="function")
    def dataset(self, test_org, context):
        step("Create data set")
        _, dataset = data_catalog.create_dataset_from_link(context, org_guid=test_org.guid,
                                                           source=self.TEST_FILE_URL)
        return dataset

    @priority.high
    def test_delete_dataset(self, test_org, dataset):
        """
        <b>Description:</b>
        Check that dataset can be deleted.

        <b>Input data:</b>
        1. dataset
        2. organization id

        <b>Expected results:</b>
        Test passes when dataset can be deleted and is not on the dataset list.

        <b>Steps:</b>
        1. Delete dataset.
        2. Check that deleted dataset is not on the dataset list.
        """
        step("Delete the data set")
        dataset.api_delete()
        step("Get data set list and check the deleted one is not on it")
        datasets = DataSet.api_get_list(org_guid_list=[test_org.guid])
        assert dataset not in datasets

    @priority.low
    def test_cannot_delete_data_set_twice(self, dataset):
        """
        <b>Description:</b>
        Try to delete a dataset twice.

        <b>Input data:</b>
        1. dataset

        <b>Expected results:</b>
        Test passes when platform returns an 404 http status when trying to delete already deleted dataset.

        <b>Steps:</b>
        1. Delete dataset.
        2. Try to delete already deleted dataset.
        """
        step("Delete data set")
        dataset.api_delete()
        step("Try to delete the dataset again")
        with pytest.raises(UnexpectedResponseError) as e:
            dataset.api_delete()
        assert e.value.status == HttpStatus.CODE_NOT_FOUND

    @priority.medium
    @pytest.mark.public_dataset
    def test_change_private_to_public_to_private(self, dataset):
        """
        <b>Description:</b>
        Check that dataset acces rights can be updated from private to public and from public to private.

        <b>Input data:</b>
        1. dataset

        <b>Expected results:</b>
        Test passes when dataset access rights can be updated from private to public and from public to private.

        <b>Steps:</b>
        1. Update dataset from private to public.
        2. Check that dataset is public.
        3. Update dataset from public to private.
        4. Check that dataset is private
        """
        step("Update data set from private to public")
        dataset.api_update(is_public=True)
        step("Check that private data set was changed to public")
        self._assert_updated(dataset.id, "is_public", True)
        step("Update data set from public to private")
        dataset.api_update(is_public=False)
        step("Check that public data set was changed to private")
        self._assert_updated(dataset.id, "is_public", False)

    @priority.low
    def test_update_data_set_category(self, dataset):
        """
        <b>Description:</b>
        Check that dataset access rights can be updated from private to public and from public to private.

        <b>Input data:</b>
        1. dataset

        <b>Expected results:</b>
        Test passes when dataset access rights can be updated from private to public and from public to private.

        <b>Steps:</b>
        1. Update dataset from private to public.
        2. Check that dataset is public.
        3. Update dataset from public to private.
        4. Check that dataset is private
        """
        new_category = next(c for c in DataSet.CATEGORIES if c != dataset.category)
        step("Update data set, change category")
        dataset.api_update(category=new_category)
        self._assert_updated(dataset.id, "category", new_category)

    @priority.low
    def test_update_dataset_to_non_existing_category(self, dataset):
        """
        <b>Description:</b>
        Check that dataset category can be updated to nonexisting value.

        <b>Input data:</b>
        1. dataset

        <b>Expected results:</b>
        Test passes when dataset category can be updated to nonexisting value.

        <b>Steps:</b>
        1. Update dataset category to nonexisting value.
        2. Check that dataset category changed to chosen category.
        """
        new_category = "user_category"
        step("Update data set with new category")
        dataset.api_update(category=new_category)
        self._assert_updated(dataset.id, "category", new_category)
