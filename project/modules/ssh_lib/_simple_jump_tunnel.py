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

import config
from modules.tap_logger import get_logger
from ._jump_client import JumpClient


class SimpleJumpTunnel(object):
    _logger = get_logger(__name__)
    _LOCALHOST = "localhost"

    def __init__(self):
        self._jump_client = JumpClient(config.ng_jump_user)
        self._local_port = config.ng_socks_proxy_port
        self._tunnel = None

    @property
    def _tunnel_command(self):
        return self._jump_client.ssh_command + ["-D", str(self._local_port), "-N"]

    def open(self):
        self._logger.info("Open tunnel with '{}'".format(" ".join(self._tunnel_command)))
        self._tunnel = subprocess.Popen(self._tunnel_command)
        try:
            self._logger.info("Wait until tunnel is established")
            self._check_tunnel_established()
        except:
            self.close()
            raise

    def close(self):
        self._logger.debug("Close local ssh tunnel")
        self._tunnel.kill()

    @retry(ConnectionRefusedError, tries=20, delay=5)
    def _check_tunnel_established(self):
        sock = socket.create_connection((self._LOCALHOST, self._local_port))
        sock.close()
