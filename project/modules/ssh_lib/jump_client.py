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
import socket
import subprocess

from retry import retry

from modules import command
from modules.tap_logger import get_logger


class JumpClient(object):
    logger = get_logger(__name__)

    def __init__(self, remote_username, remote_host, remote_key_path):
        assert remote_key_path is not None, "No ssh key specified for {}".format(remote_host)
        remote_key_path = os.path.expanduser(remote_key_path)
        assert os.path.isfile(remote_key_path), "No such file {}".format(remote_key_path)
        self.remote_username = remote_username
        self.remote_host = remote_host
        self.remote_key_path = remote_key_path

    @property
    def _auth_options(self):
        return ["-o UserKnownHostsFile=/dev/null",
                "-o StrictHostKeyChecking=no",
                "-o GSSAPIAuthentication=no",
                "-i", self.remote_key_path]

    @property
    def _user_at_hostname(self):
        return "{}@{}".format(self.remote_username, self.remote_host)

    def execute_ssh_command(self, remote_command):
        if not isinstance(remote_command, list):
            remote_command = [remote_command]
        remote_command = ["ssh"] + self._auth_options + [self._user_at_hostname] + remote_command
        return command.run(remote_command)

    def scp(self, source_path, target_path):
        remote_command = ["scp"] + self._auth_options + ["{}:{}".format(self._user_at_hostname, source_path), target_path]
        proc = subprocess.Popen(target_path)
        try:
            self.logger.debug("Waiting for scp file to download")
            self._check_if_proc_finished(proc, remote_command)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise

    @retry(subprocess.TimeoutExpired, tries=5, delay=30)
    def _check_if_proc_finished(self, proc, remote_command):
        if proc.poll() is None:
            raise subprocess.TimeoutExpired(remote_command, "")
