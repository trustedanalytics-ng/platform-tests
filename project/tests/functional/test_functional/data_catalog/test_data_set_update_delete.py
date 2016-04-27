#
# Copyright (c) 2015-2016 Intel Corporation
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

from retry import retry
from modules.constants import HttpStatus, TapComponent as TAP, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import cleanup_after_failed_setup, TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import DataSet, Organization, Transfer, User


@log_components()
@components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class UpdateDeleteDataSet(TapTestCase):
    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def setUp(self):
        self.step("Create new transfer")
        transfer = Transfer.api_create(org_guid=self.org.guid, source=Urls.test_transfer_link, is_public=False,
                                       category=DataSet.CATEGORIES[0])
        self.step("Wait for transfer to finish")
        transfer.ensure_finished()
        self.step("Get data set matching to transfer")
        self.dataset = DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    @retry(AssertionError, tries=10, delay=3)
    def _assert_updated(self, data_set_id, updated_attribute_name, expected_value):
        updated_dataset = DataSet.api_get(data_set_id)
        updated_value = getattr(updated_dataset, updated_attribute_name)
        self.assertEqual(updated_value, expected_value, "Data set was not updated")

    @priority.high
    def test_delete_dataset(self):
        self.step("Delete the data set")
        self.dataset.api_delete()
        self.step("Get data set list and check the deleted one is not on it")
        datasets = DataSet.api_get_list(org_list=[self.org])
        self.assertNotIn(self.dataset, datasets)

    @priority.low
    def test_cannot_delete_data_set_twice(self):
        self.step("Delete data set")
        self.dataset.api_delete()
        self.step("Try to delete the dataset again")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY, self.dataset.api_delete)

    @priority.medium
    def test_change_private_to_public_to_private(self):
        self.step("Update data set from private to public")
        self.dataset.api_update(is_public=True)
        self.step("Check that private data set was changed to public")
        self._assert_updated(self.dataset.id, "is_public", True)
        self.step("Update data set from public to private")
        self.dataset.api_update(is_public=False)
        self.step("Check that public data set was changed to private")
        self._assert_updated(self.dataset.id, "is_public", False)

    @priority.low
    def test_update_data_set_category(self):
        new_category = next(c for c in DataSet.CATEGORIES if c != self.dataset.category)
        self.step("Update data set, change category")
        self.dataset.api_update(category=new_category)
        self._assert_updated(self.dataset.id, "category", new_category)

    @priority.low
    def test_update_dataset_to_non_existing_category(self):
        new_category = "user_category"
        self.step("Update data set with new category")
        self.dataset.api_update(category=new_category)
        self._assert_updated(self.dataset.id, "category", new_category)
