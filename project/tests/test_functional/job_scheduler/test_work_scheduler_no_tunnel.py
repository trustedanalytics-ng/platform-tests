#
# Copyright (c) 2016 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from modules.constants import TapComponent as TAP
from modules.service_tools.psql import PsqlTable, PsqlRow
from modules.tap_logger import step
from modules.tap_object_model import HdfsJob
from modules.tap_object_model.flows import data_catalog
from modules.markers import components, priority, incremental
from modules.constants.services import ServiceLabels
from tests.fixtures.test_data import TestData
from tests.fixtures import assertions

logged_components = (TAP.workflow_scheduler,)
pytestmark = [components.workflow_scheduler]


class Psql(object):

    @classmethod
    def get_credentials(cls, app):
        psql_credentials = app.get_credentials(service_name=ServiceLabels.PSQL)
        return (psql_credentials["hostname"], psql_credentials["dbname"], psql_credentials["username"],
                psql_credentials["password"], psql_credentials["port"])


@incremental
@priority.medium
@pytest.mark.usefixtures("test_org", "test_space", "add_admin_to_test_org", "psql_app", "login_to_cf")
class TestJobSchedulerNoTunnelIncremental:

    TEST_JOB = None
    JOB_FREQUENCY_AMOUNT = 5
    JOB_FREQUENCY_UNIT = "minutes"
    ZONE_ID = "Europe/Warsaw"
    IMPORT_MODE = "Incremental"
    JOB_OUTPUT_FILES_LIST = []
    TEST_DATASET = None

    TEST_TABLE = None
    TEST_TABLE_NAME = "oh_hai"
    TEST_COLUMNS = [{"name": "col0", "type": "character varying", "max_len": 15},
                    {"name": "col1", "type": "integer", "is_nullable": False},
                    {"name": "col2", "type": "boolean", "is_nullable": True}]
    TEST_ROW = [{"column_name": "col0", "value": "kitten"}, {"column_name": "col1", "value": 1000000000},
                {"column_name": "col2", "value": True}]
    PSQL_CREDENTIALS = None

    HDFS_CONFIG_DIR = ""
    HDFS_OUTPUT_DIR = ""

    HDFS_CONFIG_FILES = ["/coordinator.xml", "/workflow.xml"]
    HDFS_OUTPUT_FILES = ["/part-m-00000", "/part-m-00001"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def prepare_test(cls, test_org, test_space, add_admin_to_test_org, login_to_cf, psql_app):
        step("Create a table in postgres DB")
        cls.TEST_TABLE = PsqlTable.post(TestData.psql_app, cls.TEST_TABLE_NAME, cls.TEST_COLUMNS)
        PsqlRow.post(TestData.psql_app, cls.TEST_TABLE_NAME, cls.TEST_ROW)

        step("Get psql credentials")
        PSQL_CREDENTIALS = Psql.get_credentials(TestData.psql_app)
        cls.db_hostname, cls.db_name, cls.username, cls.password, cls.port = PSQL_CREDENTIALS

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def cleanup_test(cls, request, class_context):
        cls.context = class_context

        def fin():
            for table in PsqlTable.TABLES:
                table.delete()
        request.addfinalizer(fin)

    @priority.low
    def test_0_create_job(self):
        self.__class__.TEST_JOB = HdfsJob.api_create(
            TestData.test_org.guid, frequency_amount=self.JOB_FREQUENCY_AMOUNT,
            frequency_unit=self.JOB_FREQUENCY_UNIT, zone_id=self.ZONE_ID, check_column="col1",
            import_mode=self.IMPORT_MODE, db_hostname=self.db_hostname, db_name=self.db_name, port=self.port,
            last_value=0, password=self.password, table=self.TEST_TABLE_NAME, target_dir="", username=self.username,
            end_job_minutes_later=15)
        assertions.assert_in_with_retry(self.TEST_JOB, HdfsJob.api_get_list, TestData.test_org.guid)
        self.TEST_JOB.ensure_successful(TestData.test_org.guid)
        self.__class__.HDFS_CONFIG_DIR = self.TEST_JOB.app_path
        self.__class__.HDFS_OUTPUT_DIR = self.TEST_JOB.target_dirs[0]

    @priority.low
    @pytest.mark.skip("DPNG-7980 HDFS files added by Job Scheduler should be available for file submit in Data Catalog")
    def test_1_check_dataset_from_HDFS(self):
        datasets = data_catalog.create_datasets_from_links(self.context, TestData.test_org, [self.HDFS_CONFIG_DIR +
                                                           source for source in self.HDFS_CONFIG_FILES])
        assertions.assert_datasets_not_empty(datasets)

        _, self.__class__.TEST_DATASET = data_catalog.create_dataset_from_link(
            self.context, TestData.test_org, self.HDFS_OUTPUT_DIR + self.HDFS_OUTPUT_FILES[0])
        assert self.TEST_DATASET.size > 0

    @priority.low
    @pytest.mark.skip("DPNG-7980 HDFS files added by Job Scheduler should be available for file submit in Data Catalog")
    def test_2_check_new_dataset_from_HDFS(self):
        PsqlRow.post(TestData.psql_app, self.TEST_TABLE_NAME, self.TEST_ROW)
        assertions.assert_dataset_greater_with_retry(self.TEST_DATASET.size, self.context, TestData.test_org,
                                                     self.HDFS_OUTPUT_DIR + self.HDFS_OUTPUT_FILES[1])

