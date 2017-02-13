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

from modules.constants import TapComponent as TAP
from modules.file_utils import download_file, get_csv_data
from modules.hive import Hive
from modules.http_calls import hue
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model.flows.data_catalog import create_dataset_from_link
from modules.test_names import escape_hive_name

logged_components = (TAP.data_catalog, TAP.dataset_publisher, TAP.das)
pytestmark = [pytest.mark.components(TAP.dataset_publisher)]


@priority.medium
@incremental
class TestHue:
    def test_0_create_transfer_and_dataset_with_csv_link(self, class_context, test_org, test_data_urls):
        """
        <b>Description:</b>
        Create transfer and dataset from an url and publish created dataset in hue.

        <b>Input data:</b>
        1. test organization

        <b>Expected results:</b>
        Test passes when transfer and dataset are successfully created and dataset is published in hue.

        <b>Steps:</b>
        1. Create transfer and dataset.
        2. Publish created dataset in hue.
        """
        step("Create new transfer and dataset")
        self.__class__.transfer, dataset = create_dataset_from_link(context=class_context, org_guid=test_org.guid,
                                                                    source=test_data_urls.test_transfer.url)
        step("Publish dataset in HUE")
        dataset.api_publish()

    @pytest.mark.bugs("DPNG-15157 502 Bad Gateway - on viewing dataset in hue")
    def test_1_check_database(self, test_org):
        """
        <b>Description:</b>
        Check that in hue there is a corresponding organization database.

        <b>Input data:</b>
        1. test organization

        <b>Expected results:</b>
        Test passes when there is a corresponding organization database in hue.

        <b>Steps:</b>
        1. Decode organization id to database name.
        2. Check if database name exists in hue database list.
        """
        step("Check organization database is on the list of hive databases")
        self.__class__.database_name = escape_hive_name(test_org.guid)
        response = hue.get_databases()
        assert self.database_name in response["databases"]

    def test_2_check_table(self):
        """
        <b>Description:</b>
        Check that its possible to get table metadata.

        <b>Input data:</b>
        1. transfer title
        2. database name

        <b>Expected results:</b>
        Test passes when there is table for created dataset and when 'status' property in table metadata equals 0

        <b>Steps:</b>
        1. Get table list.
        2. Check that there is a table named after dataset/transfer.
        3. Get table metadata.
        4. Check that status property in table metadata equals 0
        """
        step("Check there is a table with transfer title as name")
        tables_response = hue.get_tables(database_name=self.database_name)
        assert self.transfer.title in tables_response["table_names"]
        step("Try to get table metadata")
        table_metadata = hue.get_table_metadata(database_name=self.database_name, table_name=self.transfer.title)
        assert table_metadata["status"] == 0

    def test_3_check_table_content(self, test_data_urls):
        """
        <b>Description:</b>
        Check that table content is correct.

        <b>Input data:</b>
        1. transfer title
        2. database name

        <b>Expected results:</b>
        Test passes when table content, number of rows and columns are equal with source file.

        <b>Steps:</b>
        1. Compare all values from hue table with values in source file.
        2. Check that number of rows in hue table is equal to rows in csv file.
        3. Check that number of columns in hue table is equal to columns in csv file.
        """
        step("Check table content against submitted transfer")
        table_response = hue.get_table(database_name=self.database_name, table_name=self.transfer.title)
        assert table_response["rows"] == get_csv_data(test_data_urls.test_transfer.filepath)

    def test_4_check_file_browser(self, admin_user):
        """
        <b>Description:</b>
        Check that hue file browser returns correct home directory.

        <b>Input data:</b>
        1. admin user id

        <b>Expected results:</b>
        Test passes when hue returns a correct home directory path.

        <b>Steps:</b>
        1. Compare home directory returned from hue with expected home directory for admin user.
        """
        step("Check File Browser")
        response = hue.get_file_browser()
        assert response["home_directory"] == "/user/{}".format(admin_user.guid)

    def test_5_check_jobs_in_job_browser(self, admin_user):
        """
        <b>Description:</b>
        Check that hue job browser works.

        <b>Input data:</b>
        1. admin user id

        <b>Expected results:</b>
        Test passes when hue job browser returns jobs created by admin user.

        <b>Steps:</b>
        1. Check that hue returns jobs created by admin user.
        """
        step("Check jobs in job browser")
        response = hue.get_job_browser()
        assert all(item["user"] == admin_user.guid for item in response["jobs"])

    def test_6_execute_hive_queries(self, test_data_urls):
        """
        <b>Description:</b>
        Check that SQL queries can be executed in hive.

        <b>Input data:</b>
        No input data

        <b>Expected results:</b>
        Test passes when query returns a test csv file content and the record count is correct.

        <b>Steps:</b>
        1. Execute query for file contetnt.
        2. Execute query for record count.
        3. Compare that content and record count are the same as in the test csv file.
        """
        step("Connect to hive")
        hive = Hive()
        step("Execute SQL queries in hive")
        hive_data = hive.exec_query("SELECT * FROM {};".format(self.transfer.title), self.database_name)
        step("Check data from hive is equal to data from transfer")
        assert hive_data == get_csv_data(test_data_urls.test_transfer.filepath)
