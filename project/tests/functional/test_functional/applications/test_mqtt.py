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
import signal
import ssl
import subprocess
import time

import paho.mqtt.client as mqtt

from modules import app_sources
from configuration import config
from modules.constants import TapComponent as TAP, ServiceLabels, TapGitHub
from modules.http_calls import cloud_foundry as cf
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import priority, components
from modules.tap_object_model import Application, Organization, ServiceInstance, Space


@log_components()
@components(TAP.mqtt_demo, TAP.service_catalog)
class Mqtt(TapTestCase):
    SOURCES_OWNER = TapGitHub.intel_data
    REPO_NAME = TapGitHub.mqtt_demo
    INFLUX_INSTANCE_NAME = "mqtt-demo-db"
    MQTT_INSTANCE_NAME = "mqtt-demo-messages"
    TEST_DATA_FILE = os.path.join("fixtures", "shuttle_scale_cut_val.csv")
    MQTT_SERVER = "{}.{}".format(REPO_NAME, config.CONFIG["domain"])
    SERVER_CERTIFICATE = os.path.join("fixtures", "mosquitto_demo_cert.pem")
    MQTT_TOPIC_NAME = "space-shuttle/test-data"

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUp(self):

        self.step("Clone repository")
        mqtt_demo_sources = app_sources.AppSources(repo_name=self.REPO_NAME, repo_owner=self.SOURCES_OWNER,
                                                   gh_auth=config.CONFIG["github_auth"])
        app_repo_path = mqtt_demo_sources.clone_or_pull()
        self.step("Compile the sources")
        mqtt_demo_sources.compile_mvn()

        self.step("Create test organization and space")
        test_org = Organization.api_create()
        test_space = Space.api_create(test_org)

        self.step("Create required service instances.")
        ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.INFLUX_DB,
            name=self.INFLUX_INSTANCE_NAME,
            service_plan_name="free"
        )
        ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.MOSQUITTO,
            name=self.MQTT_INSTANCE_NAME,
            service_plan_name="free"
        )

        self.step("Login to cf")
        cf.cf_login(test_org.name, test_space.name)

        self.step("Push mqtt app to cf")
        mqtt_demo_app = Application.push(source_directory=app_repo_path, name=self.REPO_NAME, space_guid=test_space.guid)

        self.step("Retrieve credentials for mqtt service instance")
        self.credentials = mqtt_demo_app.get_credentials(service_name=ServiceLabels.MOSQUITTO)

    @priority.medium
    def test_mqtt_demo(self):
        """DPNG-3929 Mosquitto crendentials support-> DPNG-6067 Mosquitto ports are not accessible externally"""
        mqtt_port = self.credentials.get("port")
        self.assertIsNotNone(mqtt_port)
        mqtt_username = self.credentials.get("username")
        self.assertIsNotNone(mqtt_username)
        mqtt_pwd = self.credentials.get("password")
        self.assertIsNotNone(mqtt_pwd)

        self.step("Connect to {} with mqtt client".format(self.MQTT_SERVER))
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(mqtt_username, mqtt_pwd)
        mqtt_client.tls_set(self.SERVER_CERTIFICATE, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_client.connect(self.MQTT_SERVER, int(mqtt_port), 20)
        with open(self.TEST_DATA_FILE) as f:
            expected_data = f.read().split("\n")

        self.step("Start reading logs")
        logs = subprocess.Popen(["cf", "logs", "mqtt-demo"], stdout=subprocess.PIPE)
        time.sleep(5)

        self.step("Send {0} data vectors to {1}:{2} on topic {3}".format(len(expected_data), self.MQTT_SERVER,
                                                                         mqtt_port, self.MQTT_TOPIC_NAME))
        for line in expected_data:
            mqtt_client.publish(self.MQTT_TOPIC_NAME, line)

        self.step("Stop reading logs. Retrieve vectors from log content.")
        grep = subprocess.Popen(["grep", "message:"], stdin=logs.stdout, stdout=subprocess.PIPE)
        logs.stdout.close()
        time.sleep(50)
        os.kill(logs.pid, signal.SIGTERM)
        cut = subprocess.Popen("cut -d ':' -f7 ", stdin=grep.stdout, stdout=subprocess.PIPE, shell=True)
        grep.stdout.close()
        self.step("Check that logs display all the vectors sent")
        log_result = cut.communicate()[0].decode().split("\n")
        log_result = [item.strip() for item in log_result if item not in (" ", "")]
        self.maxDiff = None  # allows for full diff to be displayed
        self.assertListEqual(log_result, expected_data, "Data in logs do not match sent data")
