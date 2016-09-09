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

import socket
import subprocess

from retry import retry

from .jump_client import JumpClient
from modules.tap_logger import get_logger


class JumpTunnel(JumpClient):
    logger = get_logger(__name__)

    def __init__(self, host, port, remote_username, remote_host, remote_key_path):
        self._host = host
        self._port = port
        self._tunnel = None
        super().__init__(remote_username, remote_host, remote_key_path)

    @retry(ConnectionRefusedError, tries=20, delay=5)
    def _check_tunnel_established(self):
        sock = socket.create_connection((self._host, self._port))
        sock.close()

    def open(self):
        tunnel_command = ["ssh"] + self._auth_options + ["-N", "-D", self._port] + self._user_at_hostname
        self.logger.info("Opening tunnel {}".format(" ".join(tunnel_command)))
        self._tunnel = subprocess.Popen(tunnel_command)
        try:
            self.logger.info("Wait until tunnel is established")
            self._check_tunnel_established()
        except:
            self.close()
            raise

    def close(self):
        self._tunnel.kill()
