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
import time

import pytest
from retry import retry

import config
from modules.app_sources import AppSources
from modules.constants import ServiceLabels, TapComponent as TAP, TapGitHub, ServicePlan
from modules.webhdfs_tools import WebhdfsTools
from modules.ssh_client import SshTunnel
from modules.markers import components, incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance
from tests.fixtures import fixtures
from modules.websocket_client import WebsocketClient

logged_components = (TAP.ingestion_ws_kafka_hdfs, TAP.service_catalog)
pytestmark = [components.ingestion_ws_kafka_hdfs, components.service_catalog]


@incremental
@priority.medium
class TestWs2kafka2hdfs:

    REPO_OWNER = TapGitHub.intel_data
    MESSAGE_COUNT = 10
    KERBEROS_INSTANCE_NAME = "kerberos-service"
    ENDPOINT_APP_STATS = "status/stats"
    KAFKA_INSTANCE_NAME = "kafka-inst"
    ZOOKEEPER_INSTANCE_NAME = "zookeeper-inst"
    HDFS_INSTANCE_NAME = "hdfs-inst"
    messages = ["Test-{}".format(n) for n in range(MESSAGE_COUNT)]
    app_ws2kafka = None
    app_kafka2hdfs = None
    topic_name = None

    @pytest.fixture(scope="class")
    def setup_kafka_zookeeper_hdfs_instances(self, request, test_org, test_space):
        step("Create instances for kafka, zookeeper, hdfs and kerberos")

        kafka = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                          service_label=ServiceLabels.KAFKA,
                                                          name=self.KAFKA_INSTANCE_NAME,
                                                          service_plan_name=ServicePlan.SHARED)
        zookeeper = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                              service_label=ServiceLabels.ZOOKEEPER,
                                                              name=self.ZOOKEEPER_INSTANCE_NAME,
                                                              service_plan_name=ServicePlan.SHARED)
        hdfs = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                         service_label=ServiceLabels.HDFS,
                                                         name=self.HDFS_INSTANCE_NAME,
                                                         service_plan_name=ServicePlan.SHARED)
        kerberos = ServiceInstance.api_create_with_plan_name(org_guid=test_org.guid, space_guid=test_space.guid,
                                                             service_label=ServiceLabels.KERBEROS,
                                                             name=self.KERBEROS_INSTANCE_NAME,
                                                             service_plan_name=ServicePlan.SHARED)

        instances = [kafka, zookeeper, hdfs, kerberos]
        request.addfinalizer(lambda: fixtures.tear_down_test_objects(instances))

    @retry(AssertionError, tries=5, delay=2)
    def _assert_message_count_in_app_stats(self, app, expected_message_count):
        step("Check that application api returns correct number of consumed messages")
        msg_count = app.api_request(path=self.ENDPOINT_APP_STATS)[0]["consumedMessages"]
        assert msg_count == expected_message_count, "Sent {} messages, collected {}".format(expected_message_count,
                                                                                            msg_count)

    @pytest.mark.usefixtures("login_to_cf")
    def test_step_0_push_ws2kafka2hdfs(self, test_space, class_context):
        step("Clone and compile ingestion app sources")
        github_auth = config.github_credentials()
        ingestion_repo = AppSources.from_github(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=self.REPO_OWNER,
                                                gh_auth=github_auth)
        ws2kafka_path = os.path.join(ingestion_repo.path, TapGitHub.ws2kafka)
        kafka2hdfs_path = os.path.join(ingestion_repo.path, TapGitHub.kafka2hdfs)
        ingestion_repo.compile_gradle(working_directory=kafka2hdfs_path)

        postfix = str(int(time.time()))
        self.__class__.topic_name = "topic-{}".format(postfix)

        step("Push application ws2kafka")
        self.__class__.app_ws2kafka = Application.push(class_context, space_guid=test_space.guid,
                                                       source_directory=ws2kafka_path,
                                                       name="ws2kafka-{}".format(postfix),
                                                       bound_services=(self.KAFKA_INSTANCE_NAME,))
        step("Push application kafka2hdfs")
        self.__class__.app_kafka2hdfs = Application.push(class_context, space_guid=test_space.guid,
                                                         source_directory=kafka2hdfs_path,
                                                         name="kafka2hdfs-{}".format(postfix),
                                                         bound_services=(self.KAFKA_INSTANCE_NAME,
                                                                         self.ZOOKEEPER_INSTANCE_NAME,
                                                                         self.HDFS_INSTANCE_NAME,
                                                                         self.KERBEROS_INSTANCE_NAME),
                                                         env={"TOPICS": self.topic_name,
                                                              "CONSUMER_GROUP": "group-{}".format(postfix)})

        assert self.app_ws2kafka.is_started is True, "ws2kafka app is not started"
        assert self.app_kafka2hdfs.is_started is True, "kafka2hdfs app is not started"

    def test_step_1_send_from_ws2kafka2hdfs(self):
        connection_string = "{}/{}".format(self.app_ws2kafka.urls[0], self.topic_name)
        self._send_ws_messages(connection_string)
        self._assert_message_count_in_app_stats(self.app_kafka2hdfs, self.MESSAGE_COUNT)

    def test_step_2_check_messages_in_hdfs(self):
        step("Get details of broker guid")
        broker_guid = self.app_kafka2hdfs.get_credentials("hdfs")["uri"].split("/", 3)[3]
        step("Get messages from hdfs")
        hdfs_messages = self._get_messages_from_hdfs(os.path.join(broker_guid, "from_kafka", self.topic_name))
        step("Check that all sent messages are on hdfs")
        assert sorted(hdfs_messages) == sorted(self.messages)

    def _send_ws_messages(self, connection_string):
        step("Send messages to {}".format(connection_string))
        cert_requirement = None
        ws_protocol = WebsocketClient.WS
        if config.ssl_validation:
            cert_requirement = ssl.CERT_NONE
            ws_protocol = WebsocketClient.WSS
        url = "{}://{}".format(ws_protocol, connection_string)
        ws = WebsocketClient(url, certificate_requirement=cert_requirement)
        for message in self.messages:
            ws.send(message)
        ws.close()

    def _get_messages_from_hdfs(self, hdfs_path):
        ssh_tunnel = SshTunnel(config.cdh_master_2_hostname, WebhdfsTools.VIA_HOST_USERNAME,
                               path_to_key=WebhdfsTools.PATH_TO_KEY, port=WebhdfsTools.DEFAULT_PORT, via_port=22,
                               via_hostname=config.jumpbox_hostname, local_port=WebhdfsTools.DEFAULT_PORT)
        ssh_tunnel.connect()
        try:
            webhdfs_client = WebhdfsTools.create_client(host="localhost")
            hdfs = WebhdfsTools()
            topic_content = hdfs.open_and_read(webhdfs_client, hdfs_path)
        finally:
            ssh_tunnel.disconnect()
        return [m for m in topic_content.split("\n")[:-1]]
