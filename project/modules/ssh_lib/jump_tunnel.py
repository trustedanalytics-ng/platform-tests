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

import config
from .jump_client import JumpClient
from modules.tap_logger import get_logger


class JumpTunnel(object):
    _logger = get_logger(__name__)
    _LOCALHOST = "localhost"

    def __init__(self):
        self._username = config.ng_jump_user
        self._jump_client = JumpClient(self._username)
        self._ssh_command = self._jump_client.ssh_command
        self._auth_options = self._jump_client.auth_options
        self._key_path = config.ng_jump_key_path
        self._local_port = config.ng_socks_proxy_port
        self._master_0_host = config.master_0_hostname
        self._home_directory = os.path.join("/home", self._username)
        self._tunnel = None

        if config.access_to_core_services_from_jump:
            self._tunnel_command = self._ssh_command + ["-D", str(self._local_port)]
        else:
            self._logger.warning("Kubernetes not available directly from jumpbox.")
            self._copy_key_to_remote_host()
            self._tunnel_command = self._ssh_command + ["-L", "{0}:{1}:{0}".format(self._local_port, self._LOCALHOST),
                                                        "ssh {} {} -D {} bash".format(" ".join(self._auth_options),
                                                                                      self._master_0_host,
                                                                                      self._local_port)]

    def open(self):
        self._logger.info("Open tunnel '{}'".format(" ".join(self._tunnel_command)))
        self._tunnel = subprocess.Popen(self._tunnel_command)
        try:
            self._logger.info("Wait until tunnel is established")
            self._check_tunnel_established()
        except:
            self.close()
            raise

    def close(self):
        self._logger.debug("Close ssh tunnel to jumpbox")
        self._tunnel.kill()

    @retry(ConnectionRefusedError, tries=20, delay=5)
    def _check_tunnel_established(self):
        sock = socket.create_connection((self._LOCALHOST, self._local_port))
        sock.close()

    def _copy_key_to_remote_host(self):
        """
        Required when access to kubernetes and core tap services is not available on jump, only on master-0.
        """
        self._logger.info("Copy key to jump")
        target_path = os.path.join(self._home_directory, ".ssh", "id_rsa")
        self._jump_client.scp_to_remote(source_path=self._key_path, target_path=target_path)
        self._jump_client.ssh("chmod 600 {}".format(target_path))

