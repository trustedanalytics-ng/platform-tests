#
# Copyright (c) 2015-2016 Intel Corporation
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

from retry import retry
import websocket

from configuration import config
from modules.app_sources import AppSources
from modules.constants import Priority, ServiceLabels, TapComponent as TAP, TapGitHub
from modules.hdfs import Hdfs
from modules.http_calls import cloud_foundry as cf
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, incremental
from modules.tap_object_model import Application, Organization, ServiceInstance, Space, Upsi
from tests.fixtures import teardown_fixtures


@log_components()
@incremental(Priority.medium)
@components(TAP.ingestion_ws_kafka_hdfs, TAP.service_catalog)
class Ws2kafka2hdfs(TapTestCase):

    REPO_OWNER = TapGitHub.intel_data
    MESSAGE_COUNT = 10
    KERBEROS_SERVICE = "kerberos-service"
    ENDPOINT_APP_STATS = "status/stats"
    SHARED_SERVICE_PLAN_NAME = "shared"
    KAFKA_INSTANCE_NAME = "kafka-inst"
    ZOOKEEPER_INSTANCE_NAME = "zookeeper-inst"
    HDFS_INSTANCE_NAME = "hdfs-inst"
    messages = ["Test-{}".format(n) for n in range(MESSAGE_COUNT)]
    app_ws2kafka = None
    app_kafka2hdfs = None
    topic_name = None

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Clone and compile app sources")
        github_auth = config.CONFIG["github_auth"]
        ingestion_repo = AppSources(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=cls.REPO_OWNER, gh_auth=github_auth)
        ingestion_path = ingestion_repo.clone_or_pull()
        cls.ws2kafka_path = os.path.join(ingestion_path, TapGitHub.ws2kafka)
        cls.kafka2hdfs_path = os.path.join(ingestion_path, TapGitHub.kafka2hdfs)
        ingestion_repo.compile_gradle(working_directory=cls.kafka2hdfs_path)

        cls.step("Create test organization and space")
        test_org = Organization.api_create()
        cls.test_space = Space.api_create(test_org)

        cls.step("Create instances for kafka, zookeeper, hdfs")
        ServiceInstance.api_create(org_guid=test_org.guid, space_guid=cls.test_space.guid,
                                   service_label=ServiceLabels.KAFKA, name=cls.KAFKA_INSTANCE_NAME,
                                   service_plan_name=cls.SHARED_SERVICE_PLAN_NAME)
        ServiceInstance.api_create(org_guid=test_org.guid, space_guid=cls.test_space.guid,
                                   service_label=ServiceLabels.ZOOKEEPER, name=cls.ZOOKEEPER_INSTANCE_NAME,
                                   service_plan_name=cls.SHARED_SERVICE_PLAN_NAME)
        ServiceInstance.api_create(org_guid=test_org.guid, space_guid=cls.test_space.guid,
                                   service_label=ServiceLabels.HDFS, name=cls.HDFS_INSTANCE_NAME,
                                   service_plan_name=cls.SHARED_SERVICE_PLAN_NAME)

        cls.step("Get credentials for kerberos-service")
        user_provided_services = Upsi.cf_api_get_list()
        kerb_upsi = next((upsi for upsi in user_provided_services if upsi.name == cls.KERBEROS_SERVICE), None)
        cls.assertIsNotNone(kerb_upsi, "{} not found".format(cls.KERBEROS_SERVICE))
        credentials = kerb_upsi.credentials

        cls.step("Create user-provided service instance for kerberos-service in test space")
        Upsi.cf_api_create(name=cls.KERBEROS_SERVICE, space_guid=cls.test_space.guid, credentials=credentials)

        cls.step("Login to cf, targeting created org and space")
        cf.cf_login(test_org.name, cls.test_space.name)

        cls.ws_opts = {"cert_reqs": ssl.CERT_NONE}
        cls.ws_protocol = "ws://"
        if config.CONFIG["ssl_validation"]:
            cls.ws_opts = {}
            cls.ws_protocol = "wss://"

    @retry(AssertionError, tries=5, delay=2)
    def _assert_message_count_in_app_stats(self, app, expected_message_count):
        self.step("Check that application api returns correct number of consumed messages")
        msg_count = app.api_request(path=self.ENDPOINT_APP_STATS)[0]["consumedMessages"]
        self.assertEqual(msg_count, expected_message_count,
                         "Sent {} messages, collected {}".format(expected_message_count, msg_count))

    def test_step_1_push_ws2kafka2hdfs(self):
        """DPNG-5225 [hadoop-utils] remove the need for kerberos-service in non-kerberos envs"""
        postfix = str(int(time.time()))
        self.__class__.topic_name = "topic-{}".format(postfix)
        self.step("Push application ws2kafka")
        self.__class__.app_ws2kafka = Application.push(
            space_guid=self.test_space.guid,
            source_directory=self.ws2kafka_path,
            name="ws2kafka-{}".format(postfix)
        )
        self.step("Push application kafka2hdfs")
        self.__class__.app_kafka2hdfs = Application.push(
            space_guid=self.test_space.guid,
            source_directory=self.kafka2hdfs_path,
            name="kafka2hdfs-{}".format(postfix),
            bound_services=(self.KAFKA_INSTANCE_NAME, self.ZOOKEEPER_INSTANCE_NAME, self.HDFS_INSTANCE_NAME,
                            self.KERBEROS_SERVICE),
            env={"TOPICS": self.topic_name, "CONSUMER_GROUP": "group-{}".format(postfix)}
        )
        self.assertTrue(self.app_ws2kafka.is_started, "ws2kafka app is not started")
        self.assertTrue(self.app_kafka2hdfs.is_started, "kafka2hdfs app is not started")

    def test_step_2_send_from_ws2kafka2hdfs(self):
        connection_string = "{}/{}".format(self.app_ws2kafka.urls[0], self.topic_name)
        self._send_ws_messages(connection_string)
        self._assert_message_count_in_app_stats(self.app_kafka2hdfs, self.MESSAGE_COUNT)

    def test_step_3_check_messages_in_hdfs(self):
        """DPNG-5173 Cannot access hdfs directories using ec2-user"""
        self.step("Get details of broker guid")
        broker_guid = self.app_kafka2hdfs.get_credentials("hdfs")["uri"].split("/", 3)[3]
        self.step("Get messages from hdfs")
        hdfs_messages = self._get_messages_from_hdfs("/" + os.path.join(broker_guid, "from_kafka", self.topic_name))
        self.step("Check that all sent messages are on hdfs")
        self.assertUnorderedListEqual(hdfs_messages, self.messages)

    def _send_ws_messages(self, connection_string):
        self.step("Send messages to {}".format(connection_string))
        ws = websocket.create_connection("{}{}".format(self.ws_protocol, connection_string), sslopt=self.ws_opts)
        for message in self.messages:
            ws.send(message)

    def _get_messages_from_hdfs(self, hdfs_path):
        hdfs = Hdfs()
        topic_content = hdfs.cat(hdfs_path)
        return [m for m in topic_content.split("\n")[:-1]]

