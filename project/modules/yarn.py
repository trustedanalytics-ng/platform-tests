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

import config
from modules.tap_logger import get_logger


logger = get_logger(__name__)


class YarnAppStatus(object):
    RUNNING = "RUNNING"
    KILLED = "KILLED"


class Yarn(object):
    def __init__(self):
        raise NotImplementedError("Will be refactored in DPNG-8548")
        self.ssh_client = CdhMasterClient(config.cdh_master_0_hostname)
        self.yarn_app = ["yarn", "application"]

    def _execute(self, commands):
        stdout, _ = self.ssh_client.exec_commands(commands)[0]
        return stdout

    def get_application_details(self, app_id):
        command = self.yarn_app + ["--status", app_id]
        if config.kerberos:
            command = ["sudo", "su", "-", "hdfs", "-c", "'{}'".format(" ".join(command))]  # run command as a hdfs user
        output = self._execute([command])
        output = output.replace("\t", "")  # delete tabulators
        output = output.replace(" ", "")  # delete spaces
        rows = output.split("\n")[1:]  # first line contains report title
        app_details = {}
        for row in rows:
            key, value = row.split(":", 1)
            app_details.update({key: value})
        return app_details
