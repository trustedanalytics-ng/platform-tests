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

import pytest
from retry import retry
import websocket

from configuration import config
from modules.app_sources import AppSources
from modules.constants import ServiceLabels, TapComponent as TAP, TapGitHub
from modules.hdfs import Hdfs
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, incremental, priority
from modules.tap_object_model import Application, ServiceInstance, Upsi
from tests.fixtures import fixtures, test_data


logged_components = (TAP.ingestion_ws_kafka_hdfs, TAP.service_catalog)
pytestmark = [components.ingestion_ws_kafka_hdfs, components.service_catalog]


@incremental
@priority.medium
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

    @pytest.fixture(scope="class")
    def setup_kafka_zookeeper_hdfs_instances(self, request, test_org, test_space):
        self.step("Create instances for kafka, zookeeper, hdfs")
        kafka = ServiceInstance.api_create(org_guid=test_org.guid, space_guid=test_space.guid,
                                           service_label=ServiceLabels.KAFKA, name=self.KAFKA_INSTANCE_NAME,
                                           service_plan_name=self.SHARED_SERVICE_PLAN_NAME)
        zookeeper = ServiceInstance.api_create(org_guid=test_org.guid, space_guid=test_space.guid,
                                               service_label=ServiceLabels.ZOOKEEPER, name=self.ZOOKEEPER_INSTANCE_NAME,
                                               service_plan_name=self.SHARED_SERVICE_PLAN_NAME)
        hdfs = ServiceInstance.api_create(org_guid=test_org.guid, space_guid=test_space.guid,
                                          service_label=ServiceLabels.HDFS, name=self.HDFS_INSTANCE_NAME,
                                          service_plan_name=self.SHARED_SERVICE_PLAN_NAME)
        instances = [kafka, zookeeper, hdfs]
        request.addfinalizer(lambda: fixtures.tear_down_test_objects(instances))

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def delete_pushed_apps(cls, request, setup_kafka_zookeeper_hdfs_instances):
        def fin():
            test_objects = [a for a in [cls.app_ws2kafka, cls.app_kafka2hdfs] if a is not None]
            fixtures.tear_down_test_objects(test_objects)
        request.addfinalizer(fin)

    @pytest.fixture(scope="class", autouse=True)
    def workaround_for_kerberos_service(self, request, test_space, setup_kafka_zookeeper_hdfs_instances):
        self.step("Get credentials for kerberos-service")
        user_provided_services = Upsi.cf_api_get_list()
        kerb_upsi = next((upsi for upsi in user_provided_services if upsi.name == self.KERBEROS_SERVICE), None)
        self.assertIsNotNone(kerb_upsi, "{} not found".format(self.KERBEROS_SERVICE))
        credentials = kerb_upsi.credentials
        self.step("Create user-provided service instance for kerberos-service in test space")
        Upsi.cf_api_create(name=self.KERBEROS_SERVICE, space_guid=test_space.guid, credentials=credentials)

    @retry(AssertionError, tries=5, delay=2)
    def _assert_message_count_in_app_stats(self, app, expected_message_count):
        self.step("Check that application api returns correct number of consumed messages")
        msg_count = app.api_request(path=self.ENDPOINT_APP_STATS)[0]["consumedMessages"]
        self.assertEqual(msg_count, expected_message_count,
                         "Sent {} messages, collected {}".format(expected_message_count, msg_count))

    @pytest.mark.usefixtures("login_to_cf")
    @pytest.mark.bugs("DPNG-5225 [hadoop-utils] remove the need for kerberos-service in non-kerberos envs")
    def test_step_0_push_ws2kafka2hdfs(self):
        self.step("Clone and compile ingestion app sources")
        github_auth = config.CONFIG["github_auth"]
        ingestion_repo = AppSources(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=self.REPO_OWNER, gh_auth=github_auth)
        ingestion_path = ingestion_repo.clone_or_pull()
        ws2kafka_path = os.path.join(ingestion_path, TapGitHub.ws2kafka)
        kafka2hdfs_path = os.path.join(ingestion_path, TapGitHub.kafka2hdfs)
        ingestion_repo.compile_gradle(working_directory=kafka2hdfs_path)

        postfix = str(int(time.time()))
        self.__class__.topic_name = "topic-{}".format(postfix)

        self.step("Push application ws2kafka")
        self.__class__.app_ws2kafka = Application.push(
            space_guid=test_data.TestData.test_space.guid,
            source_directory=ws2kafka_path,
            name="ws2kafka-{}".format(postfix)
        )
        self.step("Push application kafka2hdfs")
        self.__class__.app_kafka2hdfs = Application.push(
            space_guid=test_data.TestData.test_space.guid,
            source_directory=kafka2hdfs_path,
            name="kafka2hdfs-{}".format(postfix),
            bound_services=(self.KAFKA_INSTANCE_NAME, self.ZOOKEEPER_INSTANCE_NAME, self.HDFS_INSTANCE_NAME,
                            self.KERBEROS_SERVICE),
            env={"TOPICS": self.topic_name, "CONSUMER_GROUP": "group-{}".format(postfix)}
        )

        self.assertTrue(self.app_ws2kafka.is_started, "ws2kafka app is not started")
        self.assertTrue(self.app_kafka2hdfs.is_started, "kafka2hdfs app is not started")

    def test_step_1_send_from_ws2kafka2hdfs(self):
        connection_string = "{}/{}".format(self.app_ws2kafka.urls[0], self.topic_name)
        self._send_ws_messages(connection_string)
        self._assert_message_count_in_app_stats(self.app_kafka2hdfs, self.MESSAGE_COUNT)

    @pytest.mark.bugs("DPNG-5173 Cannot access hdfs directories using ec2-user")
    def test_step_2_check_messages_in_hdfs(self):
        self.step("Get details of broker guid")
        broker_guid = self.app_kafka2hdfs.get_credentials("hdfs")["uri"].split("/", 3)[3]
        self.step("Get messages from hdfs")
        hdfs_messages = self._get_messages_from_hdfs("/" + os.path.join(broker_guid, "from_kafka", self.topic_name))
        self.step("Check that all sent messages are on hdfs")
        self.assertUnorderedListEqual(hdfs_messages, self.messages)

    def _send_ws_messages(self, connection_string):
        self.step("Send messages to {}".format(connection_string))
        ws_opts = {"cert_reqs": ssl.CERT_NONE}
        ws_protocol = "ws://"
        if config.CONFIG["ssl_validation"]:
            ws_opts = {}
            ws_protocol = "wss://"
        ws = websocket.create_connection("{}{}".format(ws_protocol, connection_string), sslopt=ws_opts)
        for message in self.messages:
            ws.send(message)

    def _get_messages_from_hdfs(self, hdfs_path):
        hdfs = Hdfs()
        topic_content = hdfs.cat(hdfs_path)
        return [m for m in topic_content.split("\n")[:-1]]
