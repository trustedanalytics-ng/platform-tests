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

import config
from modules.tap_logger import get_logger
from ._jump_client import JumpClient
from ._remote_process import RemoteProcess
from ._simple_jump_tunnel import SimpleJumpTunnel


class NestedJumpTunnel(SimpleJumpTunnel):
    _logger = get_logger(__name__)
    _LOCALHOST = "localhost"
    _KEY_COPIED = False
    _DEFAULT_JUMP_PORT = 5555
    _PORT_OPTION = "-D"

    def __init__(self):
        super().__init__()
        self._username = config.ng_jump_user
        self._jump_client = JumpClient(self._username)
        self._home_directory_on_jump = os.path.join("/home", self._username)
        self._ssh_command = self._jump_client.ssh_command
        self._auth_options = self._jump_client.auth_options
        self._key_path = self._jump_client.key_path
        self._local_port = config.ng_socks_proxy_port
        self._master_0_host = config.master_0_hostname
        self._remote_tunnel_command_no_port = "ssh {} {} -N -D ".format(" ".join(self._auth_options), self._master_0_host)
        self._local_tunnel_command = ["-L", "{0}:{1}:{0}".format(self._local_port, self._LOCALHOST)]
        self.__jump_port = None

    @property
    def _remote_tunnel_command(self):
        """
        Before remote tunnel command is built, available port on jumpbox is first established.
        """
        return self._remote_tunnel_command_no_port + str(self._get_available_jump_port())

    @property
    def _tunnel_command(self):
        self._logger.warning("Kubernetes not available directly from jumpbox.")
        self._copy_key_to_remote_host()
        return self._ssh_command + self._local_tunnel_command + [self._remote_tunnel_command]

    def close(self):
        """
        First, close tunnel process started on jumpbox.
        Second, close tunnel process started locally.
        """
        self._logger.debug("Close ssh tunnel on jumpbox")
        tunnel_process_on_jump = self._find_tunnel_process_on_jump()
        if tunnel_process_on_jump is None:
            self._logger.warning("Tunnel process does not seem to exist on jumpbox")
        else:
            tunnel_process_on_jump.kill()
        super().close()

    def _copy_key_to_remote_host(self):
        """
        Required when access to kubernetes and core tap services is not available on jump, only on master-0.
        """
        if not self._KEY_COPIED:
            self._logger.info("Copy key to jump")
            target_path = os.path.join(self._home_directory_on_jump, ".ssh", "id_rsa")
            self._jump_client.scp_to_remote(source_path=self._key_path, target_path=target_path)
            self._jump_client.ssh("chmod 600 {}".format(target_path))
            self.__class__._KEY_COPIED = True

    @classmethod
    def _get_port_from_remote_tunnel_command(cls, actual_command):
        assert cls._PORT_OPTION in actual_command, "Process command does not include '{}'".format(cls._PORT_OPTION)
        index = actual_command.index(cls._PORT_OPTION)
        try:
            port = actual_command[index:].split(" ")[1]
            return int(port, 10)
        except (ValueError, IndexError):
            raise ValueError("Did not find port in command '{}'".format(actual_command))

    def _get_available_jump_port(self):
        """
        Search for an available port on jumpbox - only on the first call.
        This method is suboptimal, it looks only for processes started by this class.
        We'll see if it works.
        """
        if self.__jump_port is None:
            jump_processes = RemoteProcess.get_list(ssh_client=self._jump_client)
            busy_ports = []
            for process in jump_processes:
                if self._remote_tunnel_command_no_port in process.command:
                    port = self._get_port_from_remote_tunnel_command(process.command)
                    self._logger.warning("Port {} on jumpbox is busy".format(port))
                    busy_ports.append(port)
            for port in range(self._DEFAULT_JUMP_PORT, self._DEFAULT_JUMP_PORT + 100):
                if port not in busy_ports:
                    self.__jump_port = port
                    break
        return self.__jump_port

    def _find_tunnel_process_on_jump(self):
        jump_processes = RemoteProcess.get_list(ssh_client=self._jump_client)
        for process in jump_processes:
            if self._remote_tunnel_command in process.command and self._username in process.user:
                return process