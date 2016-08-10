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

import json

import pytest

import config
from modules.app_sources import AppSources
from modules.constants import ServicePlan, ServiceLabels, TapGitHub, TapComponent as TAP
from modules.markers import incremental, priority
from modules.service_tools.psql import PsqlRow, PsqlTable
from modules.ssh_client import DirectSshClient, SshTunnel
from modules.tap_logger import step
from modules.tap_object_model import Application, HdfsJob, ServiceInstance, ServiceType
from modules.tap_object_model.hdfs_job import JobStatus
from modules.test_names import generate_test_object_name
from modules.webhdfs_tools import WebhdfsTools
from tests.fixtures import assertions
from tests.fixtures.db_input import DbInput


logged_components = (TAP.workflow_scheduler,)
pytestmark = [pytest.mark.components(TAP.workflow_scheduler)]


@incremental
@priority.medium
@pytest.mark.skipif(config.kerberos, reason="DPNG-8628 WebHDFS needs to be workable on environments with kerberos")
class TestYarnAuthGateway:
    ssh_tunnel = None

    TEST_HOST = "localhost"

    test_job = None
    END_JOB_MINUTES_LATER = 15
    JOB_FREQUENCY_AMOUNT = 5
    JOB_FREQUENCY_UNIT = "minutes"
    IMPORT_MODE = "Append"
    ZONE_ID = "Europe/Warsaw"
    job_output_files_list = []
    hdfs_output_dir = ""

    test_table_name = None
    TEST_COLUMNS = DbInput.test_columns
    TEST_ROWS = DbInput.test_rows_0[0]

    psql_app = None
    kerberos_instance = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def prepare_ssh_tunnel_and_finalizer(self, request):
        step("Create tunnel to {}".format(config.cdh_master_0_hostname))
        self.SSH_TUNNEL = SshTunnel(hostname=config.cdh_master_0_hostname, username=config.jumpbox_username,
                                    path_to_key=config.jumpbox_key_path, port=WebhdfsTools.DEFAULT_PORT,
                                    via_hostname=config.jumpbox_hostname, via_port=22,
                                    local_port=WebhdfsTools.DEFAULT_PORT)
        self.SSH_TUNNEL.connect()

        def fin():
            self.SSH_TUNNEL.disconnect()
            for table in PsqlTable.TABLES:
                table.delete()

        request.addfinalizer(fin)

    def test_0_create_kerberos_instance(self, class_context, test_org, test_space):
        step("Check kerberos in marketplace")
        service_label = ServiceLabels.KERBEROS
        marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
        kerberos = next((service for service in marketplace if service.label == service_label), None)
        assert kerberos is not None, "{} not available".format(service_label)
        step("Create instance of kerberos")
        self.__class__.kerberos_instance = ServiceInstance.api_create_with_plan_name(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=service_label,
            service_plan_name=ServicePlan.SHARED
        )
        self.kerberos_instance.ensure_created()
        step("Check that the kerberos is on the instances list")
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert self.kerberos_instance in instances

    def test_1_push_app_to_cf(self, class_context, test_space, psql_instance, login_to_cf):
        step("Push application to cf")
        sql_api_sources = AppSources.get_repository(repo_name=TapGitHub.sql_api_example,
                                                    repo_owner=TapGitHub.intel_data)
        self.__class__.psql_app = Application.push(context=class_context, source_directory=sql_api_sources.path,
                                                   space_guid=test_space.guid,
                                                   bound_services=(psql_instance.name, self.kerberos_instance.name))
        step("Check the application is running")
        assertions.assert_equal_with_retry(True, self.psql_app.cf_api_app_is_running)
        step("Check that application is on the list")
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert self.psql_app in apps

    def test_2_post_data(self):
        step("Create test table name")
        self.__class__.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        step("Pass POST request to the application")
        PsqlTable.post(self.psql_app, self.test_table_name, self.TEST_COLUMNS)
        tables = str(PsqlTable.get_list(self.psql_app))
        step("Check that table with name '{}' was created.".format(self.test_table_name))
        assert self.test_table_name in tables, "There is no '{}' table in database".format(self.test_table_name)
        step("Fill postgres table with data")
        PsqlRow.post(self.psql_app, self.test_table_name, self.TEST_ROWS)
        step("Check if there is data in table")
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        assert len(rows) >= 1, "There is no data in table"

    def test_3_create_job(self, test_org, add_admin_to_test_org):
        step("Get PSQL credentials")
        psql_credentials = self.psql_app.get_credentials(service_name=ServiceLabels.PSQL)
        step("Create job")
        self.__class__.test_job = HdfsJob.api_create(
            org_guid=test_org.guid, name=None, frequency_amount=self.JOB_FREQUENCY_AMOUNT,
            frequency_unit=self.JOB_FREQUENCY_UNIT, zone_id=self.ZONE_ID, check_column="", import_mode=self.IMPORT_MODE,
            db_hostname=psql_credentials["hostname"], db_name=psql_credentials["dbname"], port=psql_credentials["port"],
            last_value="", password=psql_credentials["password"], table=self.test_table_name, target_dir="",
            username=psql_credentials["username"], end_job_minutes_later=self.END_JOB_MINUTES_LATER)
        step("Check job is on the list")
        assertions.assert_in_with_retry(self.test_job, HdfsJob.api_get_list, test_org.guid)
        step("Check job succeded")
        self.test_job.ensure_successful(test_org.guid)
        assert self.test_job.status == JobStatus.SUCCEEDED.value
        self.__class__.hdfs_output_dir = self.test_job.target_dirs[0].split("nameservice1/")[1]

    def test_4_check_data_on_hdfs(self):
        step("Check job in Web HDFS")
        webhdfs = WebhdfsTools.create_client(host=self.TEST_HOST)
        self.__class__.job_output_files_list = self.test_job.get_files_list(webhdfs, self.hdfs_output_dir)
        assert len(self.job_output_files_list) > 0
        job_output_file_content = self.test_job.get_file_content(webhdfs, self.hdfs_output_dir,
                                                                 self.job_output_files_list[0])
        HdfsJob.check_response(job_output_file_content, [self.TEST_ROWS])

    def test_5_check_job_in_cloudera(self, admin_user, core_space):
        step("Connect to bastion")
        client = DirectSshClient(hostname=config.jumpbox_hostname, username=config.jumpbox_username,
                                 path_to_key=config.jumpbox_key_path)
        client.connect()
        step("Check job in cloudera manager")
        app_name = TAP.cdh_broker
        cdh_broker = next((app for app in Application.cf_api_get_list_by_space(core_space.guid)
                           if app_name in app.name), None)
        assert cdh_broker is not None, "{} not available".format(app_name)
        url = str(json.loads(cdh_broker.cf_api_env()["ENVIRONMENT_JSON"]["CREDENTIALS"])["resource_manager"]).\
            replace(config.cdh_master_0_hostname, "cdh-master-1")
        cluster = str(client.exec_command("curl {}/cluster".format(url)))
        user_guid_and_job_name = "\"{}\",\"oozie:action:T=sqoop:W={}".format(admin_user.guid, self.test_job.app_name)
        assert user_guid_and_job_name in cluster, "Job is not visible in log with user guid"
        client.disconnect()
