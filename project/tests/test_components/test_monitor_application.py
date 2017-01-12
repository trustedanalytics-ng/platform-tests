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
import re

import pytest

from modules.constants import TapComponent as TAP
from modules.tap_logger import step
from modules.http_calls.kubernetes import k8s_get_pods, k8s_logs

pytestmark = [pytest.mark.components(TAP.monitor)]

@pytest.mark.usefixtures("open_tunnel")
class TestMonitorApplication:
    LOG_TIME_SEC = 300

    def test_app_deployment(self, sample_python_app):
        """
        <b>Description:</b>
        Check monitor during app deployment

        <b>Input data:</b>
        Sample application

        <b>Expected results:</b>
        Monitor logs can be retrieved

        <b>Steps:</b>
        - Update application manifest
        - Push the application and wait for it to receive id
        - Retrieve applicaiton logs
        - Verify presence of monitor logs
        """
        pods = k8s_get_pods()
        items = pods["items"]
        for k in items:
            try:
                if k["metadata"]["labels"]["app"] != TAP.container_broker:
                    continue
            except KeyError:
                continue

            container_broker_name = k["metadata"]["name"]

        step("Collect logs for container-broker")
        log = k8s_logs(container_broker_name, {"sinceSeconds": self.LOG_TIME_SEC,
                                               "container": "container-broker"})
        log_entries = log.split('\n')
        step("Look through the log entries to find id of application in monitor")
        for k in log_entries:
            if "{}".format(sample_python_app.id) not in k:
                continue

            m = re.search(r'instanceId=([-0-9a-zA-Z]*)', k)
            if m is None:
                continue
            print(m.group(1))
            monitor_app_id = m.group(1)
            break

        monitor_logs = [i for i in log_entries if "[MonitorInstanceDeployments]" in i and """Updating Instance state to: RUNNING. InstanceId: {}. Last message: Started container with docker id""".format(monitor_app_id)]
        assert len(monitor_logs) != 0


        step("Restart the application and retrieve the logs")
        sample_python_app.restart()
        sample_python_app.ensure_running()
        step("Collect logs for container-broker")
        log = k8s_logs(container_broker_name, {"sinceSeconds": self.LOG_TIME_SEC,
                                               "container": "container-broker"})
        log_entries = log.split('\n')

        monitor_logs = [i for i in log_entries if "[MonitorInstanceDeployments]" in i and """Updating Instance state to: RUNNING. InstanceId: {}. Last message: Killing container with docker id""".format(monitor_app_id)]
        assert len(monitor_logs) != 0
