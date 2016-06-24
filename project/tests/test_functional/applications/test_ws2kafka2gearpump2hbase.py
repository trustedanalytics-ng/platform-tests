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

import pytest

from configuration import config
from modules.app_sources import AppSources
from modules.constants import TapComponent as TAP, ServiceLabels, Urls, TapGitHub, ServicePlan
from modules.file_utils import download_file
from modules.hbase_client import HbaseClient
from modules.markers import components, incremental, priority
from modules.service_tools.gearpump import Gearpump
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance
from modules.test_names import generate_test_object_name
from modules.websocket_client import WebsocketClient
from tests.fixtures import fixtures

logged_components = (TAP.ingestion_ws_kafka_gearpump_hbase, TAP.service_catalog)
pytestmark = [components.ingestion_ws_kafka_gearpump_hbase, components.service_catalog]


@incremental
@priority.medium
class TestWs2kafka2gearpump2hbase:

    REPO_OWNER = TapGitHub.intel_data
    TOPIC_NAME = "myFavouriteKafkaTopic"
    WS2KAFKA_APP_NAME = "ws2kafka"
    HBASE_API_APP_NAME = "hbase-reader"
    KAFKA2HBASE_APP_NAME = "kafka2hbase"
    HBASE_TABLE_NAME = "pipeline"
    ONE_WORKER_PLAN_NAME = ServicePlan.WORKER_1
    SHARED_PLAN_NAME = ServicePlan.SHARED
    BARE_PLAN_NAME = ServicePlan.BARE
    hbase_namespace = None
    db_and_table_name = None

    @pytest.fixture(scope="class", autouse=True)
    def setup_kafka_zookeeper_hbase_instances(self, request, test_org, test_space):
        step("Create instances of kafka, zookeeper, hbase")

        kafka = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                          service_label=ServiceLabels.KAFKA, name="kafka-inst",
                                                          service_plan_name=self.SHARED_PLAN_NAME)
        zookeeper = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                              service_label=ServiceLabels.ZOOKEEPER,
                                                              name="zookeeper-inst",
                                                              service_plan_name=self.SHARED_PLAN_NAME)
        hbase = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                          service_label=ServiceLabels.HBASE, name="hbase1",
                                                          service_plan_name=self.BARE_PLAN_NAME)
        kerberos = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                             service_label=ServiceLabels.KERBEROS,
                                                             name="kerberos-instance",
                                                             service_plan_name=self.SHARED_PLAN_NAME)
        test_instances = [kafka, zookeeper, hbase, kerberos]
        request.addfinalizer(lambda: fixtures.tear_down_test_objects(test_instances))

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def push_apps(cls, test_org, test_space, login_to_cf, setup_kafka_zookeeper_hbase_instances, class_context):
        step("Get ws2kafka app sources")
        github_auth = config.CONFIG["github_auth"]
        ingestion_repo = AppSources.from_github(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=cls.REPO_OWNER,
                                                gh_auth=github_auth)
        ws2kafka_path = os.path.join(ingestion_repo.path, TapGitHub.ws2kafka)

        step("Get hbase reader app sources")
        hbase_reader_repo = AppSources.from_github(repo_name=TapGitHub.hbase_api_example, repo_owner=cls.REPO_OWNER,
                                                   gh_auth=github_auth)
        hbase_reader_repo.compile_gradle()

        step("Push apps")
        cls.app_ws2kafka = Application.push(class_context, space_guid=test_space.guid,
                                            source_directory=ws2kafka_path,
                                            name=generate_test_object_name(short=True),
                                            env_proxy=config.CONFIG["pushed_app_proxy"])
        app_hbase_reader = Application.push(class_context, space_guid=test_space.guid,
                                            source_directory=hbase_reader_repo.path,
                                            name=generate_test_object_name(short=True),
                                            env_proxy=config.CONFIG["pushed_app_proxy"])
        cls.hbase_reader = HbaseClient(app_hbase_reader)

    def _send_messages(self, connection_string):
        step("Send messages to {}".format(connection_string))
        cert_requirement = None
        ws_protocol = WebsocketClient.WS
        if config.CONFIG["ssl_validation"]:
            cert_requirement = ssl.CERT_NONE
            ws_protocol = WebsocketClient.WSS
        url = "{}://{}".format(ws_protocol, connection_string)
        messages = ["Test-{}".format(n) for n in range(2)]
        ws = WebsocketClient(url, certificate_requirement=cert_requirement)
        for message in messages:
            ws.send(message)
        ws.close()

    def test_0_create_gearpump_instance(self, test_org, test_space):
        step("Create gearpump instance")
        self.__class__.gearpump = Gearpump(test_org.guid, test_space.guid,
                                           service_plan_name=self.ONE_WORKER_PLAN_NAME)
        step("Check that gearpump instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        if self.gearpump.instance not in instances:
            raise AssertionError("gearpump instance is not on list of instances")
        self.gearpump.get_credentials()

    def test_1_login_to_gearpump_ui(self):
        step("Log into gearpump UI")
        self.gearpump.login()

    def test_step_2_get_hbase_namespace(self):
        step("Get hbase namespace from hbase-reader env")
        self.__class__.hbase_namespace = self.hbase_reader.get_namespace()
        assert self.hbase_namespace is not None, "hbase namespace is not set"
        self.__class__.db_and_table_name = "{}:{}".format(self.hbase_namespace, self.HBASE_TABLE_NAME)

    def test_step_3_create_hbase_table(self):
        step("Create hbase table pipeline")
        self.hbase_reader.create_table(self.HBASE_TABLE_NAME)
        step("Check that pipeline table was created")
        hbase_tables = self.hbase_reader.get_tables()
        assert self.db_and_table_name in hbase_tables is True, "No pipeline table"

    def test_step_4_submit_kafka2hbase_app_to_gearpump_dashboard(self):
        step("Download file kafka2hbase")
        kafka2hbase_app_path = download_file(url=Urls.kafka2hbase_app_url,
                                             save_file_name=Urls.kafka2hbase_app_url.split("/")[-1])
        step("Submit application kafka2hbase to gearpump dashboard")
        kafka2hbase_app = self.gearpump.submit_application_jar(kafka2hbase_app_path, self.KAFKA2HBASE_APP_NAME)
        step("Check that submitted application is started")
        assert kafka2hbase_app.is_started is True, "kafka2hbase app is not started"

    def test_step_5_send_from_ws2kafka(self):
        connection_string = "{}/{}".format(self.app_ws2kafka.urls[0], self.TOPIC_NAME)
        self._send_messages(connection_string)

    @unittest.skip("DPNG-6031")
    def test_step_6_get_hbase_table_rows(self):
        pipeline_rows = self.hbase_reader.get_first_rows_from_table(self.db_and_table_name)
        step("Check that messages from kafka were sent to hbase")
        assert self.MESSAGES[0][::-1] in pipeline_rows and self.MESSAGES[1][::-1] in pipeline_rows is True,"No messages in hbase"
