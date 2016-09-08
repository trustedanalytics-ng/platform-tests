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

import ssl

import pytest
from retry import retry

import config
from modules.app_sources import AppSources
from modules.constants import TapComponent as TAP, ServiceLabels, TapGitHub, ServicePlan
from modules.file_utils import download_file
from modules.hbase_client import HbaseClient
from modules.markers import incremental, priority
from modules.service_tools.gearpump import Gearpump
from modules.tap_logger import step
from modules.test_names import generate_test_object_name
from modules.websocket_client import WebsocketClient

logged_components = (TAP.ingestion_ws_kafka_gearpump_hbase, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.ingestion_ws_kafka_gearpump_hbase, TAP.service_catalog)]


@incremental
@priority.medium
@pytest.mark.sample_apps_test
class TestWs2kafka2gearpump2hbase:

    TOPIC_IN = "topicIn"
    TOPIC_OUT = "topicOut"
    HBASE_COLUMN_FAMILY = "message"
    HBASE_TABLE_NAME = "pipeline"
    GEARPUMP_PLAN_NAME = ServicePlan.SMALL
    db_and_table_name = None
    hbase_reader = None

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

    @pytest.mark.bugs("DPNG-13981 'Gearpump broker can't create new instance - 403' ")
    def test_0_create_gearpump_instance(self, class_context):
        """
        <b>Description:</b>
        Checks if gearpump instance can be created.

        <b>Input data:</b>
        1. Organization

        <b>Expected results:</b>
        Gearpump instance was created.

        <b>Steps:</b>
        1. Create instance.
        2. Verify the instance exists.
        """
        step("Create gearpump instance with plan {} ".format(self.GEARPUMP_PLAN_NAME))
        self.__class__.gearpump = Gearpump(class_context, service_plan_name=self.GEARPUMP_PLAN_NAME)
        step("Ensure that instance is running")
        self.gearpump.instance.ensure_running()
        self.gearpump.get_credentials()

    def test_1_get_hbase_namespace(self, test_org):
        """
        <b>Description:</b>
        Checks if hbase namespace can be retrieved.

        <b>Input data:</b>
        1. Hbase application.

        <b>Expected results:</b>
        Hbase namespace was retrieved.

        <b>Steps:</b>
        1. Verify the namespace.
        """
        step("Get hbase namespace")
        hbase_namespace = test_org.guid.replace("-", "")
        assert hbase_namespace is not None, "hbase namespace is not set"
        self.__class__.db_and_table_name = "{}:{}".format(hbase_namespace, self.HBASE_TABLE_NAME)

    def test_2_create_hbase_table(self, hbase_reader_app):
        """
        <b>Description:</b>
        Checks if hbase table can be created.

        <b>Input data:</b>
        1. Hbase client.

        <b>Expected results:</b>
        Hbase table was created.

        <b>Steps:</b>
        1. Create a table.
        1. Verify the table was created.
        """
        self.hbase_reader = HbaseClient(hbase_reader_app)

        step("Create hbase table pipeline")
        self.hbase_reader.create_table(self.HBASE_TABLE_NAME, column_families=[self.HBASE_COLUMN_FAMILY])
        step("Check that pipeline table was created")
        hbase_tables = self.hbase_reader.get_tables()
        assert self.db_and_table_name in hbase_tables, "No pipeline table"

    @pytest.mark.bugs("DPNG-13583 Nginx image doesn't support websocket protocol for TAP-NG apps")
    def test_3_submit_kafka2hbase_app_to_gearpump_dashboard(self, go_to_dashboard, ws2kafka_app, kafka2hdfs_app,
                                                            test_data_urls):
        """
        <b>Description:</b>
        Checks if Kafka2hbase application can be submited to gearpump dashboard.

        <b>Input data:</b>
        1. Ws2kafka application.
        2. Gearpump instance.

        <b>Expected results:</b>
        Application can be submited.

        <b>Steps:</b>
        1. Create topics.
        2. Submit the application.
        3. Verify the application was started.
        """
        step("Create input and output topics by sending messages")
        self._send_messages(ws2kafka_app.urls[0], ["init_message"], self.TOPIC_IN)
        self._send_messages(ws2kafka_app.urls[0], ["init_message"], self.TOPIC_OUT)
        step("Download file kafka2hbase")
        step("Submit application kafka2hbase to gearpump dashboard")
        extra_params = {"inputTopic": self.TOPIC_IN, "outputTopic": self.TOPIC_OUT, "tableName": self.db_and_table_name,
                        "columnFamily": self.HBASE_COLUMN_FAMILY, "hbaseUser": "cf"}
        kafka2hbase_app = self.gearpump.submit_application_jar(test_data_urls.kafka2gearpump2hbase.filename,
                                                               kafka2hdfs_app.name, extra_params,
                                                               self.instances_credentials, timeout=180)
        step("Check that submitted application is started")
        assert kafka2hbase_app.is_started, "kafka2hbase app is not started"

    def test_4_check_messages_flow(self, ws2kafka_app):
        """
        <b>Description:</b>
        Checks if messages send through ws2kafka can be retrieved by hbase application.

        <b>Input data:</b>
        1. Ws2kafka application.
        2. Hbase application.

        <b>Expected results:</b>
        Hbase can read the messages.

        <b>Steps:</b>
        1. Send messages.
        2. Verify the messages was received.
        """

        @retry(AssertionError, tries=10, delay=2)
        def _assert_messages_in_hbase():
            rows = self.hbase_reader.get_first_rows_from_table(self.db_and_table_name)
            hbase_messages = [row["columnFamilies"][0]["columnValues"][0]["value"] for row in rows]
            step("Check that messages from kafka were sent to hbase")
            assert messages[0][::-1] in hbase_messages and messages[1][::-1] in hbase_messages, \
                "No messages in hbase"

        messages = [generate_test_object_name(short=True) for _ in range(2)]
        self._send_messages(ws2kafka_app.urls[0], messages, self.TOPIC_IN)
        _assert_messages_in_hbase()
