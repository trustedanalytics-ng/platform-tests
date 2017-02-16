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
from urllib.parse import urlsplit

import pytest
from retry import retry

import config
from modules.constants import TapComponent as TAP
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.webhdfs_tools import WebhdfsTools
from modules.websocket_client import WebsocketClient

logged_components = (TAP.ingestion_ws_kafka_hdfs, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.ingestion_ws_kafka_hdfs, TAP.service_catalog)]


@incremental
@priority.medium
@pytest.mark.sample_apps_test
class TestWs2kafka2hdfs:

    MESSAGE_COUNT = 10
    ENDPOINT_APP_STATS = "status/stats"
    messages = ["Test-{}".format(n) for n in range(MESSAGE_COUNT)]
    topic_name = "topic-{}".format(str(int(time.time())))
    app_kafka2hdfs = None

    @pytest.mark.bugs("DPNG-15304 Fix tests.test_functional.applications.test_ws2kafka2hdfs")
    def test_step_0_send_from_ws2kafka2hdfs(self, ws2kafka_app, kafka2hdfs_app):
        """
        <b>Description:</b>
        Checks if a message can be sent to ws2kafka.

        <b>Input data:</b>
        1. Ws2kafka application.

        <b>Expected results:</b>
        Message can be sent.

        <b>Steps:</b>
        1. Send message.
        2. Verify message is in application stats.
        """
        self.app_kafka2hdfs = kafka2hdfs_app
        domain_name = "{0.netloc}".format(urlsplit(ws2kafka_app.urls[0]))
        connection_string = "{}/{}".format(domain_name, self.topic_name)
        self._send_ws_messages(connection_string)
        self._assert_message_count_in_app_stats(self.app_kafka2hdfs, self.MESSAGE_COUNT)

    def test_step_1_check_messages_in_hdfs(self):
        """
        <b>Description:</b>
        Checks if a message is in hdfs.

        <b>Input data:</b>
        1. Kafka2hdfs application.

        <b>Expected results:</b>
        Message can be read.

        <b>Steps:</b>
        1. Verify message was received.
        """
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
        raise NotImplementedError("Will be refactored in DPNG-8898")
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

    @retry(AssertionError, tries=5, delay=2)
    def _assert_message_count_in_app_stats(self, app, expected_message_count):
        step("Check that application api returns correct number of consumed messages")
        msg_count = app.api_request(path=self.ENDPOINT_APP_STATS)[0]["consumedMessages"]
        assert msg_count == expected_message_count, "Sent {} messages, collected {}".format(expected_message_count,
                                                                                            msg_count)
