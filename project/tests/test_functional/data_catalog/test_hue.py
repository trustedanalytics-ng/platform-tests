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

import csv

from bs4 import BeautifulSoup

from modules.constants import TapComponent as TAP, Urls
from modules.file_utils import download_file
from modules.hive import Hive
from modules.http_calls import hue
from modules.markers import components, priority, incremental
from modules.tap_logger import step
from modules.tap_object_model.flows.data_catalog import create_dataset_from_link
from modules.test_names import escape_hive_name

logged_components = (TAP.data_catalog, TAP.dataset_publisher, TAP.das)
pytestmark = [components.dataset_publisher]


@priority.medium
@incremental
class TestHue:
    TRANSFER_SOURCE = Urls.test_transfer_link

    def test_0_create_transfer_and_dataset_with_csv_link(self, class_context, test_org, add_admin_to_test_org):
        step("Create new transfer and dataset")
        self.__class__.transfer, dataset = create_dataset_from_link(context=class_context, org=test_org,
                                                                    source=self.TRANSFER_SOURCE)
        step("Publish dataset")
        dataset.api_publish()

    def test_1_check_database(self, test_org):
        step("Check organization database is on the list of hive databases")
        self.__class__.database_name = escape_hive_name(test_org.guid)
        response = hue.get_databases()
        assert self.database_name in response["databases"]
        step("Check there is a table with transfer title as name")
        tables_response = hue.get_tables(database_name=self.database_name)
        assert self.transfer.title in tables_response
        step("Check table content against submitted transfer")
        table_response = hue.get_table(database_name=self.database_name, table_name=self.transfer.title)
        expected_csv = list(csv.reader(open(download_file(url=self.TRANSFER_SOURCE))))
        table_soup = BeautifulSoup(table_response, "html.parser")
        sample_table = table_soup.find("table", {"id": "sampleTable"})
        assert all(val in str(sample_table) for val in sum(expected_csv, [])), "Not all table values are in hue"
        sample_table_soup = BeautifulSoup(str(sample_table), "html.parser")
        rows = sample_table_soup.find_all("tr")
        assert len(rows) - 1 == len(expected_csv), "The number of rows is incorrect"
        columns = sample_table_soup.find_all("th")
        assert len(columns) - 1 == 8, "The number of columns is incorrect"

    def test_2_check_file_browser(self, admin_user):
        step("Check File Browser")
        response = hue.get_file_browser()
        assert response["home_directory"] == "/user/{}".format(admin_user.guid)

    def test_3_check_jobs_in_job_browser(self, admin_user):
        step("Check jobs in job browser")
        response = hue.get_job_browser()
        assert all(item["user"] == admin_user.guid for item in response["jobs"])

    def test_4_execute_hive_queries(self):
        step("Connect to hive")
        hive = Hive()
        step("Execute SQL queries in hive")
        hive_data = hive.exec_query("SELECT * FROM {}.{};".format(self.database_name, self.transfer.title))
        record_count = hive.exec_query("SELECT COUNT(*) FROM {}.{};".format(self.database_name, self.transfer.title))
        step("Check data from hive is equal to data from transfer")
        test_csv = list(map(lambda x: x.strip(), open(download_file(url=self.TRANSFER_SOURCE)).readlines()))
        assert hive_data == test_csv
        assert record_count == [str(len(test_csv))]
