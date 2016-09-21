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

import os
import ssl

import pytest
from retry import retry

import config
from modules.app_sources import AppSources
from modules.constants import TapComponent as TAP, ServiceLabels, Urls, TapGitHub, ServicePlan
from modules.file_utils import download_file
from modules.hbase_client import HbaseClient
from modules.markers import incremental, priority
from modules.service_tools.gearpump import Gearpump
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceKey
from modules.test_names import generate_test_object_name
from modules.websocket_client import WebsocketClient

logged_components = (TAP.ingestion_ws_kafka_gearpump_hbase, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.ingestion_ws_kafka_gearpump_hbase, TAP.service_catalog)]


@incremental
@priority.medium
@pytest.mark.sample_apps_test
@pytest.mark.skip(reason="Not yet adjusted to new TAP")
class TestWs2kafka2gearpump2hbase:

    REPO_OWNER = TapGitHub.intel_data
    TOPIC_IN = "topicIn"
    TOPIC_OUT = "topicOut"
    KAFKA2HBASE_APP_NAME = "kafka2hbase"
    HBASE_COLUMN_FAMILY = "message"
    HBASE_TABLE_NAME = "pipeline"
    HBASE_INSTANCE_NAME = "hbase1"
    KAFKA_INSTANCE_NAME = "kafka-inst"
    KERBEROS_INSTANCE_NAME = "kerberos-instance"
    ZOOKEEPER_INSTANCE_NAME = "zookeeper-inst"
    ONE_WORKER_PLAN_NAME = ServicePlan.WORKER_1
    SHARED_PLAN_NAME = ServicePlan.SHARED
    BARE_PLAN_NAME = ServicePlan.BARE
    db_and_table_name = None
    test_instances = []
    instances_credentials = {}

    @pytest.fixture(scope="class", autouse=True)
    def setup_required_instances(self, class_context, test_org, test_space):
        step("Create instances of kafka, zookeeper, hbase and kerberos")

        kafka = ServiceInstance.api_create_with_plan_name(context=class_context,
                                                          org_guid=test_org.guid, space_guid=test_space.guid,
                                                          service_label=ServiceLabels.KAFKA,
                                                          name=self.KAFKA_INSTANCE_NAME,
                                                          service_plan_name=self.SHARED_PLAN_NAME)
        zookeeper = ServiceInstance.api_create_with_plan_name(context=class_context,
                                                              org_guid=test_org.guid, space_guid=test_space.guid,
                                                              service_label=ServiceLabels.ZOOKEEPER,
                                                              name=self.ZOOKEEPER_INSTANCE_NAME,
                                                              service_plan_name=self.SHARED_PLAN_NAME)
        hbase = ServiceInstance.api_create_with_plan_name(context=class_context,
                                                          org_guid=test_org.guid, space_guid=test_space.guid,
                                                          service_label=ServiceLabels.HBASE,
                                                          name=self.HBASE_INSTANCE_NAME,
                                                          service_plan_name=self.BARE_PLAN_NAME)
        kerberos = ServiceInstance.api_create_with_plan_name(context=class_context,
                                                             org_guid=test_org.guid, space_guid=test_space.guid,
                                                             service_label=ServiceLabels.KERBEROS,
                                                             name=self.KERBEROS_INSTANCE_NAME,
                                                             service_plan_name=self.SHARED_PLAN_NAME)
        self.__class__.test_instances = [kafka, zookeeper, hbase, kerberos]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def push_apps(cls, test_org, test_space, login_to_cf, setup_required_instances, class_context):
        step("Get ws2kafka app sources")
        ingestion_repo = AppSources.get_repository(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=cls.REPO_OWNER)
        ws2kafka_path = os.path.join(ingestion_repo.path, TapGitHub.ws2kafka)

        step("Get hbase reader app sources")
        hbase_reader_repo = AppSources.get_repository(repo_name=TapGitHub.hbase_api_example, repo_owner=cls.REPO_OWNER)
        hbase_reader_repo.compile_gradle()

        step("Push apps")
        cls.app_ws2kafka = Application.push(class_context, space_guid=test_space.guid,
                                            source_directory=ws2kafka_path,
                                            name=generate_test_object_name(short=True),
                                            bound_services=(cls.KAFKA_INSTANCE_NAME,))
        app_hbase_reader = Application.push(class_context, space_guid=test_space.guid,
                                            source_directory=hbase_reader_repo.path,
                                            name=generate_test_object_name(short=True),
                                            bound_services=(cls.HBASE_INSTANCE_NAME, cls.KERBEROS_INSTANCE_NAME,
                                                            cls.ZOOKEEPER_INSTANCE_NAME, cls.KAFKA_INSTANCE_NAME))
        cls.hbase_reader = HbaseClient(app_hbase_reader)

    @pytest.fixture(scope="function")
    def go_to_dashboard(self, request):
        self.gearpump.go_to_dashboard()
        request.addfinalizer(self.gearpump.go_to_console)

    def _send_messages(self, ws2kafka_url, messages, topic_name):
        connection_string = "{}/{}".format(ws2kafka_url, topic_name)
        step("Send messages to {}".format(connection_string))
        cert_requirement = None
        ws_protocol = WebsocketClient.WS
        if config.ssl_validation:
            cert_requirement = ssl.CERT_NONE
            ws_protocol = WebsocketClient.WSS
        url = "{}://{}".format(ws_protocol, connection_string)
        ws = WebsocketClient(url, certificate_requirement=cert_requirement)
        for message in messages:
            ws.send(message)
        ws.close()

    def _get_service_key_dict(self, instance):
        service_key = ServiceKey.api_create(instance.guid, instance.name)
        service_key.api_delete()
        plan = self.BARE_PLAN_NAME if instance.service_label == ServiceLabels.HBASE else self.SHARED_PLAN_NAME
        return {
            "label": instance.service_label,
            "name": instance.name,
            "tags": instance.tags,
            "credentials": service_key.credentials,
            "plan": plan
        }

    def test_0_create_gearpump_instance(self, class_context, test_org, test_space):
        step("Create gearpump instance")
        self.__class__.gearpump = Gearpump(class_context, test_org.guid, test_space.guid,
                                           service_plan_name=self.ONE_WORKER_PLAN_NAME)
        step("Check that gearpump instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        if self.gearpump.instance not in instances:
            raise AssertionError("gearpump instance is not on list of instances")
        self.gearpump.get_credentials()

    def test_1_get_api_keys(self):
        step("Create service key for each service instance and prepare credentials dictionary")
        for instance in self.test_instances:
            if instance.service_label != ServiceLabels.KERBEROS:
                key_dict = {instance.service_label: [self._get_service_key_dict(instance)]}
                self.__class__.instances_credentials.update(key_dict)

    def test_2_get_hbase_namespace(self):
        step("Get hbase namespace")
        hbase_namespace = self.instances_credentials["hbase"][0]["credentials"].get("hbase.namespace")
        assert hbase_namespace is not None, "hbase namespace is not set"
        self.__class__.db_and_table_name = "{}:{}".format(hbase_namespace, self.HBASE_TABLE_NAME)

    def test_3_create_hbase_table(self):
        step("Create hbase table pipeline")
        self.hbase_reader.create_table(self.HBASE_TABLE_NAME, column_families=[self.HBASE_COLUMN_FAMILY])
        step("Check that pipeline table was created")
        hbase_tables = self.hbase_reader.get_tables()
        assert self.db_and_table_name in hbase_tables, "No pipeline table"

    def test_4_submit_kafka2hbase_app_to_gearpump_dashboard(self, add_admin_to_test_org, go_to_dashboard):
        step("Create input and output topics by sending messages")
        self._send_messages(self.app_ws2kafka.urls[0], ["init_message"], self.TOPIC_IN)
        self._send_messages(self.app_ws2kafka.urls[0], ["init_message"], self.TOPIC_OUT)
        step("Download file kafka2hbase")
        kafka2hbase_app_path = download_file(url=Urls.kafka2gearpump2hbase,
                                             save_file_name=Urls.kafka2gearpump2hbase.split("/")[-1])
        step("Submit application kafka2hbase to gearpump dashboard")
        extra_params = {"inputTopic": self.TOPIC_IN, "outputTopic": self.TOPIC_OUT, "tableName": self.db_and_table_name,
                        "columnFamily": self.HBASE_COLUMN_FAMILY, "hbaseUser": "cf"}
        kafka2hbase_app = self.gearpump.submit_application_jar(kafka2hbase_app_path, self.KAFKA2HBASE_APP_NAME,
                                                               extra_params, self.instances_credentials, timeout=180)
        step("Check that submitted application is started")
        assert kafka2hbase_app.is_started, "kafka2hbase app is not started"

    @pytest.mark.bugs("DPNG-7938 'HBase is security enabled' error - kerberos env")
    def test_5_check_messages_flow(self):

        @retry(AssertionError, tries=10, delay=2)
        def _assert_messages_in_hbase():
            rows = self.hbase_reader.get_first_rows_from_table(self.db_and_table_name)
            hbase_messages = [row["columnFamilies"][0]["columnValues"][0]["value"] for row in rows]
            step("Check that messages from kafka were sent to hbase")
            assert messages[0][::-1] in hbase_messages and messages[1][::-1] in hbase_messages, \
                "No messages in hbase"

        messages = [generate_test_object_name(short=True) for _ in range(2)]
        self._send_messages(self.app_ws2kafka.urls[0], messages, self.TOPIC_IN)
        _assert_messages_in_hbase()
