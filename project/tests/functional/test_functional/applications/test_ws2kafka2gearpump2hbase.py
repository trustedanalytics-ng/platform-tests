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

import os
import ssl
import unittest

import websocket

from configuration import config
from modules.app_sources import AppSources
from modules.constants import TapComponent as TAP, Priority, ServiceLabels, Urls, TapGitHub
from modules.file_utils import download_file
from modules.hbase_client import HbaseClient
from modules.http_calls import cloud_foundry as cf
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, incremental
from modules.service_tools.gearpump import Gearpump
from modules.tap_object_model import Application, Organization, ServiceInstance, Space
from modules.test_names import get_test_name


@log_components()
@incremental(Priority.medium)
@components(TAP.ingestion_ws_kafka_gearpump_hbase, TAP.service_catalog)
class Ws2kafka2gearpump2hbase(TapTestCase):
    REPO_OWNER = TapGitHub.intel_data
    TOPIC_NAME = "myFavouriteKafkaTopic"
    WS2KAFKA_APP_NAME = "ws2kafka"
    HBASE_API_APP_NAME = "hbase-reader"
    KAFKA2HBASE_APP_NAME = "kafka2hbase"
    HBASE_TABLE_NAME = "pipeline"
    ONE_WORKER_PLAN_NAME = "1 worker"
    SHARED_PLAN_NAME = "shared"
    hbase_namespace = None
    db_and_table_name = None

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Clone and compile app sources")
        github_auth = config.CONFIG["github_auth"]
        ingestion_repo = AppSources(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=cls.REPO_OWNER, gh_auth=github_auth)
        ingestion_path = ingestion_repo.clone_or_pull()
        ws2kafka_path = os.path.join(ingestion_path, TapGitHub.ws2kafka)
        hbase_reader_repo = AppSources(repo_name=TapGitHub.hbase_api_example, repo_owner=cls.REPO_OWNER,
                                       gh_auth=github_auth)
        hbase_reader_path = hbase_reader_repo.clone_or_pull()
        hbase_reader_repo.compile_gradle()

        cls.step("Download file kafka2hbase")
        cls.kafka2hbase_app_path = download_file(url=Urls.kafka2hbase_app_url,
                                                 save_file_name=Urls.kafka2hbase_app_url.split("/")[-1])

        cls.step("Create test org and space")
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)

        cls.step("Create instances of kafka, zookeeper, hbase")
        ServiceInstance.api_create(org_guid=cls.test_org.guid, space_guid=cls.test_space.guid,
                                   service_label=ServiceLabels.KAFKA, name="kafka-inst",
                                   service_plan_name=cls.SHARED_PLAN_NAME)
        ServiceInstance.api_create(org_guid=cls.test_org.guid, space_guid=cls.test_space.guid,
                                   service_label=ServiceLabels.ZOOKEEPER, name="zookeeper-inst",
                                   service_plan_name=cls.SHARED_PLAN_NAME)
        ServiceInstance.api_create(org_guid=cls.test_org.guid, space_guid=cls.test_space.guid,
                                   service_label=ServiceLabels.HBASE, name="hbase1",
                                   service_plan_name=cls.SHARED_PLAN_NAME)

        cls.step("Login to cf, target test org and space")
        cf.cf_login(cls.test_org.name, cls.test_space.name)

        cls.step("Push apps")
        cls.app_ws2kafka = Application.push(space_guid=cls.test_space.guid, source_directory=ws2kafka_path,
                                            name=get_test_name(short=True))
        app_hbase_reader = Application.push(space_guid=cls.test_space.guid, source_directory=hbase_reader_path,
                                            name=get_test_name(short=True))

        cls.step("Create gearpump instance")
        cls.gearpump = Gearpump(cls.test_org.guid, cls.test_space.guid, service_plan_name=cls.ONE_WORKER_PLAN_NAME)
        cls.assert_gearpump_instance_created(gearpump_data_science=cls.gearpump.data_science,
                                             space_guid=cls.test_space.guid)

        cls.hbase_reader = HbaseClient(app_hbase_reader)
        cls.step("Log into gearpump UI")
        cls.gearpump.login()

        cls.ws_opts = {"cert_reqs": ssl.CERT_NONE}
        cls.ws_protocol = "ws://"
        if config.CONFIG["ssl_validation"]:
            cls.ws_opts = {}
            cls.ws_protocol = "wss://"

    @classmethod
    def assert_gearpump_instance_created(cls, gearpump_data_science, space_guid):
        cls.step("Check that gearpump instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        if gearpump_data_science.instance not in instances:
            raise AssertionError("gearpump instance is not on list of instances")
        gearpump_data_science.get_credentials()

    def _generate_example_messages(self, msg_count):
        return ["Test-{}".format(n) for n in range(msg_count)]

    def _send_ws_messages(self, connection_string):
        message_count = 2
        self.step("Send messages to {}".format(connection_string))
        ws = websocket.create_connection("{}{}".format(self.ws_protocol, connection_string), sslopt=self.ws_opts)
        messages = self._generate_example_messages(message_count)
        for message in messages:
            ws.send(message)
        return ws.status

    def test_step_1_get_hbase_namespace(self):
        self.step("Get hbase namespace from hbase-reader env")
        self.__class__.hbase_namespace = self.hbase_reader.get_namespace()
        self.assertIsNotNone(self.hbase_namespace, msg="hbase namespace is not set")
        self.__class__.db_and_table_name = "{}:{}".format(self.hbase_namespace, self.HBASE_TABLE_NAME)

    def test_step_2_create_hbase_table(self):
        self.step("Create hbase table pipeline")
        self.hbase_reader.create_table(self.HBASE_TABLE_NAME)
        self.step("Check that pipeline table was created")
        hbase_tables = self.hbase_reader.get_tables()
        self.assertTrue(self.db_and_table_name in hbase_tables, msg="No pipeline table")

    def test_step_3_submit_kafka2hbase_app_to_gearpump_dashboard(self):
        self.step("Submit application kafka2hbase to gearpump dashboard")
        kafka2hbase_app = self.gearpump.submit_application_jar(self.kafka2hbase_app_path, self.KAFKA2HBASE_APP_NAME)
        self.step("Check that submitted application is started")
        self.assertTrue(kafka2hbase_app.is_started, msg="kafka2hbase app is not started")

    def test_step_4_send_from_ws2kafka(self):
        connection_string = "{}/{}".format(self.app_ws2kafka.urls[0], self.TOPIC_NAME)
        status_code = self._send_ws_messages(connection_string)
        self.step("Check that status code is 101")
        self.assertTrue(status_code == 101, msg="problem with websocket connection")

    @unittest.skip("DPNG-6031")
    def test_step_5_get_hbase_table_rows(self):
        pipeline_rows = self.hbase_reader.get_first_rows_from_table(self.db_and_table_name)
        self.step("Check that messages from kafka were sent to hbase")
        self.assertTrue(self.MESSAGES[0][::-1] in pipeline_rows and self.MESSAGES[1][::-1] in pipeline_rows,
                        msg="No messages in hbase")
