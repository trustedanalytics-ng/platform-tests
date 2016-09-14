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

from modules.constants import ServiceLabels, TapComponent as TAP
from modules.markers import priority, incremental
from modules.service_tools.psql import PsqlTable, PsqlRow
from modules.tap_logger import step
from modules.tap_object_model import HdfsJob
from modules.tap_object_model.flows import data_catalog
from modules.test_names import generate_test_object_name
from tests.fixtures import assertions
from tests.fixtures.db_input import DbInput

logged_components = (TAP.workflow_scheduler,)
pytestmark = [pytest.mark.components(TAP.workflow_scheduler)]


class Psql(object):

    @classmethod
    def get_credentials(cls, app):
        psql_credentials = app.get_credentials(service_name=ServiceLabels.PSQL)
        return (psql_credentials["hostname"], psql_credentials["dbname"], psql_credentials["username"],
                psql_credentials["password"], psql_credentials["port"])


@incremental
@priority.medium
class TestJobSchedulerNoTunnelIncremental:

    TEST_JOB = None
    JOB_FREQUENCY_AMOUNT = 5
    JOB_FREQUENCY_UNIT = "minutes"
    ZONE_ID = "Europe/Warsaw"
    IMPORT_MODE = "Incremental"
    JOB_OUTPUT_FILES_LIST = []
    TEST_DATASET = None

    TEST_TABLE = None
    test_table_name = None
    TEST_COLUMNS = DbInput.test_columns
    TEST_ROWS = DbInput.test_rows_0[0]

    PSQL_CREDENTIALS = None

    HDFS_CONFIG_DIR = ""
    HDFS_OUTPUT_DIR = ""

    HDFS_CONFIG_FILES = ["/coordinator.xml", "/workflow.xml"]
    HDFS_OUTPUT_FILES = ["/part-m-00000", "/part-m-00001"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def prepare_test(cls, test_org, test_space, add_admin_to_test_org, login_to_cf, psql_app, request, class_context):
        step("Create a table in postgres DB")
        cls.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        cls.TEST_TABLE = PsqlTable.post(psql_app, cls.test_table_name, cls.TEST_COLUMNS)
        PsqlRow.post(psql_app, cls.test_table_name, cls.TEST_ROWS)
        step("Get psql credentials")
        PSQL_CREDENTIALS = Psql.get_credentials(psql_app)
        cls.db_hostname, cls.db_name, cls.username, cls.password, cls.port = PSQL_CREDENTIALS
        step("Create context")
        cls.context = class_context
        def fin():
            for table in PsqlTable.TABLES:
                table.delete()
        request.addfinalizer(fin)

    def test_0_create_job(self, test_org):
        self.__class__.TEST_JOB = HdfsJob.api_create(
            test_org.guid, frequency_amount=self.JOB_FREQUENCY_AMOUNT,
            frequency_unit=self.JOB_FREQUENCY_UNIT, zone_id=self.ZONE_ID, check_column="col1",
            import_mode=self.IMPORT_MODE, db_hostname=self.db_hostname, db_name=self.db_name, port=self.port,
            last_value=0, password=self.password, table=self.test_table_name, target_dir="", username=self.username,
            end_job_minutes_later=15)
        assertions.assert_in_with_retry(self.TEST_JOB, HdfsJob.api_get_list, test_org.guid)
        self.TEST_JOB.ensure_successful(test_org.guid)
        self.__class__.HDFS_CONFIG_DIR = self.TEST_JOB.app_path
        self.__class__.HDFS_OUTPUT_DIR = self.TEST_JOB.target_dirs[0]

    @pytest.mark.skip("DPNG-7980 HDFS files added by Job Scheduler should be available for file submit in Data Catalog")
    def test_1_check_dataset_from_HDFS(self, test_org):
        datasets = data_catalog.create_datasets_from_links(self.context, test_org.guid, [self.HDFS_CONFIG_DIR +
                                                           source for source in self.HDFS_CONFIG_FILES])
        assertions.assert_datasets_not_empty(datasets)

        _, self.__class__.TEST_DATASET = data_catalog.create_dataset_from_link(
            self.context, test_org.guid, self.HDFS_OUTPUT_DIR + self.HDFS_OUTPUT_FILES[0])
        assert self.TEST_DATASET.size > 0

    @pytest.mark.skip("DPNG-7980 HDFS files added by Job Scheduler should be available for file submit in Data Catalog")
    def test_2_check_new_dataset_from_HDFS(self, test_org, psql_app):
        PsqlRow.post(psql_app, self.test_table_name, self.TEST_ROWS)
        assertions.assert_dataset_greater_with_retry(self.TEST_DATASET.size, self.context, test_org.guid,
                                                     self.HDFS_OUTPUT_DIR + self.HDFS_OUTPUT_FILES[1])

