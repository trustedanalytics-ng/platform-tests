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

import config
from modules.constants import ServiceLabels, TapComponent as TAP
from modules.markers import priority, incremental
from modules.service_tools.psql import PsqlTable, PsqlRow
from modules.ssh_client import SshTunnel
from modules.tap_logger import step
from modules.tap_object_model import HdfsJob
from modules.test_names import generate_test_object_name
from modules.webhdfs_tools import WebhdfsTools
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
@pytest.mark.skipif(config.kerberos, reason="DPNG-8628 WebHDFS needs to be workable on environments with kerberos")
class TestJobScheduler:

    TEST_HOST = "localhost"

    TEST_JOB = None
    JOB_FREQUENCY_AMOUNT = 5
    JOB_FREQUENCY_UNIT = "minutes"
    ZONE_ID = "Europe/Warsaw"
    IMPORT_MODE = "Append"
    JOB_OUTPUT_FILES_LIST = []

    TEST_TABLE = None
    test_table_name = None
    TEST_COLUMNS = DbInput.test_columns
    TEST_ROWS = DbInput.test_rows_0

    PSQL_CREDENTIALS = None

    SSH_TUNNEL = None
    HDFS_CONFIG_DIR = ""
    HDFS_OUTPUT_DIR = ""
    WEBHDFS = None

    HDFS_CONFIG_FILES = ["coordinator.xml", "workflow.xml"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def prepare_test(cls, test_org, test_space, add_admin_to_test_org, login_to_cf, psql_app, request):
        step("Create a table in postgres DB")
        cls.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        cls.TEST_TABLE = PsqlTable.post(psql_app, cls.test_table_name, cls.TEST_COLUMNS)
        PsqlRow.post(psql_app, cls.test_table_name, cls.TEST_ROWS[0])
        step("Create tunnel to cdh-master-0")
        cls.SSH_TUNNEL = SshTunnel(hostname=config.cdh_master_0_hostname, username=config.jumpbox_username,
                                   path_to_key=config.jumpbox_key_path, port=WebhdfsTools.DEFAULT_PORT,
                                   via_hostname=config.jumpbox_hostname, via_port=22,
                                   local_port=WebhdfsTools.DEFAULT_PORT)
        cls.SSH_TUNNEL.connect()
        step("Get psql credentials")
        PSQL_CREDENTIALS = Psql.get_credentials(psql_app)
        cls.db_hostname, cls.db_name, cls.username, cls.password, cls.port = PSQL_CREDENTIALS
        cls.WEBHDFS = WebhdfsTools.create_client(host=cls.TEST_HOST)

        def fin():
            cls.SSH_TUNNEL.disconnect()
            for table in PsqlTable.TABLES:
                table.delete()

        request.addfinalizer(fin)

    def test_0_create_job(self, test_org):
        self.__class__.TEST_JOB = HdfsJob.api_create(
            test_org.guid, frequency_amount=self.JOB_FREQUENCY_AMOUNT,
            frequency_unit=self.JOB_FREQUENCY_UNIT, zone_id=self.ZONE_ID, check_column="", import_mode=self.IMPORT_MODE,
            db_hostname=self.db_hostname, db_name=self.db_name, port=self.port, last_value="", password=self.password,
            table=self.test_table_name, target_dir="", username=self.username, end_job_minutes_later=15)
        assertions.assert_in_with_retry(self.TEST_JOB, HdfsJob.api_get_list, test_org.guid)
        self.TEST_JOB.ensure_successful(test_org.guid)
        self.__class__.HDFS_CONFIG_DIR = self.TEST_JOB.app_path.split("nameservice1/")[1]
        self.__class__.HDFS_OUTPUT_DIR = self.TEST_JOB.target_dirs[0].split("nameservice1/")[1]

    def test_1_check_HDFS(self):
        job_config_files_list = self.TEST_JOB.get_files_list(self.WEBHDFS, self.HDFS_CONFIG_DIR)
        assert set(self.HDFS_CONFIG_FILES).issubset(set(job_config_files_list))
        self.__class__.JOB_OUTPUT_FILES_LIST = self.TEST_JOB.get_files_list(self.WEBHDFS, self.HDFS_OUTPUT_DIR)
        assert len(self.JOB_OUTPUT_FILES_LIST) > 0
        job_output_file_content = self.TEST_JOB.get_file_content(self.WEBHDFS, self.HDFS_OUTPUT_DIR,
                                                                 self.JOB_OUTPUT_FILES_LIST[0])
        HdfsJob.check_response(job_output_file_content, self.TEST_ROWS)

    def test_2_check_new_data_on_HDFS(self, psql_app):
        PsqlRow.post(psql_app, self.test_table_name, self.TEST_ROWS[1])
        rows = PsqlRow.get_list(psql_app, self.test_table_name)
        rows = [row.values for row in rows]
        rows = [list(row.values()) for row in rows]
        test_rows = [[x['value'] for x in row] for row in self.TEST_ROWS]
        assert [sorted([str(a) for a in r]) for r in rows] == [sorted([str(a) for a in r]) for r in test_rows]

        assertions.assert_greater_with_retry(self.TEST_JOB.get_files_list, self.JOB_OUTPUT_FILES_LIST, self.WEBHDFS,
                                             self.HDFS_OUTPUT_DIR)
        job_output_file_content_updated = self.TEST_JOB.get_file_content(self.WEBHDFS, self.HDFS_OUTPUT_DIR,
                                                                         self.TEST_JOB.get_files_list(
                                                                             self.WEBHDFS, self.HDFS_OUTPUT_DIR)[-1])
        HdfsJob.check_response(job_output_file_content_updated, self.TEST_ROWS)
