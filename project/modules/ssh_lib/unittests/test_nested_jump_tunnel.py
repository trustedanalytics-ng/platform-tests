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
from unittest import mock

import pytest

from ._mocks import MockConfig, MockSystemMethods
from modules.ssh_lib._remote_process import RemoteProcess
from modules.ssh_lib._nested_jump_tunnel import NestedJumpTunnel


class MockProcess:
    def __init__(self, cmd, user):
        self.command = cmd
        self.user = user


@mock.patch("modules.ssh_lib._jump_client.os.path.isfile", MockSystemMethods.isfile)
@mock.patch("modules.ssh_lib._jump_client.os.path.exists", MockSystemMethods.exists)
@mock.patch("modules.ssh_lib._jump_client.config", MockConfig())
class TestNestedJumpTunnel:
    CONFIG_MODULE = "modules.ssh_lib._nested_jump_tunnel.config"
    JUMP_CLIENT_CLASS = "modules.ssh_lib._nested_jump_tunnel.JumpClient"
    REMOTE_PROCESS_GET_LIST_METHOD = "modules.ssh_lib._nested_jump_tunnel.RemoteProcess.get_list"
    REMOTE_TUNNEL_COMMAND_PROPERTY = "modules.ssh_lib._nested_jump_tunnel.NestedJumpTunnel._remote_tunnel_command"
    SIMPLE_TUNNEL_CLOSE = "modules.ssh_lib._simple_jump_tunnel.SimpleJumpTunnel.close"

    MOCK_SSH_COMMAND = ["mock", "ssh", "command"]
    MOCK_AUTH_OPTIONS = ["mock", "auth", "options"]

    @pytest.fixture(scope="function")
    def jump_tunnel(self):
        with mock.patch(self.CONFIG_MODULE, MockConfig()) as mock_config:
            with mock.patch(self.JUMP_CLIENT_CLASS) as mock_client:
                mock_instance = mock_client.return_value
                mock_instance.ssh_command = self.MOCK_SSH_COMMAND
                mock_instance.auth_options = self.MOCK_AUTH_OPTIONS
                mock_instance.key_path = mock_config.ng_jump_key_path
                return NestedJumpTunnel()

    @pytest.fixture(scope="class")
    def mock_client(self):
        class Dummy:
            ssh = None
        return Dummy

    def test_init(self):
        with mock.patch(self.CONFIG_MODULE, MockConfig()) as mock_config:
            with mock.patch(self.JUMP_CLIENT_CLASS) as mock_client:
                mock_instance = mock_client.return_value
                mock_instance.ssh_command = self.MOCK_SSH_COMMAND
                mock_instance.auth_options = self.MOCK_AUTH_OPTIONS
                mock_instance.key_path = mock_config.ng_jump_key_path
                jump_tunnel = NestedJumpTunnel()
        mock_client.assert_called_with(mock_config.ng_jump_user)
        assert jump_tunnel._username == mock_config.ng_jump_user
        assert jump_tunnel._home_directory_on_jump == "/home/{}".format(mock_config.ng_jump_user)
        assert jump_tunnel._ssh_command == self.MOCK_SSH_COMMAND
        assert jump_tunnel._auth_options == self.MOCK_AUTH_OPTIONS
        assert jump_tunnel._key_path == mock_config.ng_jump_key_path
        assert jump_tunnel._local_port == mock_config.ng_socks_proxy_port
        assert jump_tunnel._master_0_host == mock_config.master_0_hostname
        assert isinstance(jump_tunnel._local_tunnel_command, list)
        assert jump_tunnel._tunnel is None
        assert jump_tunnel._NestedJumpTunnel__jump_port is None

    def test_get_port_from_remote_tunnel_command(self):
        expected_port = 12345
        test_command = "ssh -D {} -N".format(expected_port)
        port = NestedJumpTunnel._get_port_from_remote_tunnel_command(test_command)
        assert port == expected_port

    @pytest.mark.parametrize("incorrect_command", ("", " ", "ssh 12345 -N"))
    def test_get_port_from_remote_tunnel_command_no_D_option(self, incorrect_command):
        with pytest.raises(AssertionError) as e:
            NestedJumpTunnel._get_port_from_remote_tunnel_command(incorrect_command)
        assert "Process command does not include" in e.value.msg

    @pytest.mark.parametrize("incorrect_command", ("-D abcde", "ssh 12345 -D"))
    def test_get_port_from_remote_tunnel_command_no_port(self, incorrect_command):
        with pytest.raises(ValueError) as e:
            NestedJumpTunnel._get_port_from_remote_tunnel_command(incorrect_command)
        assert "Did not find port in command" in e.value.args[0]

    @mock.patch(REMOTE_PROCESS_GET_LIST_METHOD, mock.Mock(return_value=[]))
    def test_jump_port_no_processes(self, jump_tunnel):
        port = jump_tunnel._get_available_jump_port()
        assert port == NestedJumpTunnel._DEFAULT_JUMP_PORT

    def test_jump_port_some_busy(self, jump_tunnel, mock_client):
        busy_ports = [5555, 5556, 5557, 5559]
        expected_port = 5558
        commands = [jump_tunnel._remote_tunnel_command_no_port + str(bp) for bp in busy_ports]
        processes = [RemoteProcess(ssh_client=mock_client, user="u", pid=1, command=c) for c in commands]
        with mock.patch(self.REMOTE_PROCESS_GET_LIST_METHOD, mock.Mock(return_value=processes)):
            port = jump_tunnel._get_available_jump_port()
        assert port == expected_port

    def test_jump_port_is_not_retrieved_twice(self, jump_tunnel):
        with mock.patch(self.REMOTE_PROCESS_GET_LIST_METHOD, mock.Mock(return_value=[])) as mock_get_processes:
            port = jump_tunnel._get_available_jump_port
            port_b = jump_tunnel._get_available_jump_port
        mock_get_processes.assert_called_once()
        assert port == port_b

    def test_remote_tunnel_command(self, jump_tunnel):
        with mock.patch.object(jump_tunnel, "_get_available_jump_port", mock.Mock(return_value=1234)) as mock_port:
            remote_tunnel_command = jump_tunnel._remote_tunnel_command
        assert str(mock_port.return_value) in remote_tunnel_command

    def test_tunnel_command(self, jump_tunnel):
        with mock.patch(self.REMOTE_TUNNEL_COMMAND_PROPERTY, "abc") as mock_remote_tunnel_cmd:
            tunnel_command = jump_tunnel._tunnel_command
        assert tunnel_command == jump_tunnel._ssh_command + jump_tunnel._local_tunnel_command + [mock_remote_tunnel_cmd]

    def test_tunnel_process_on_jump(self, jump_tunnel):
        expected_command = "abc"
        expected_username = jump_tunnel._username
        expected_process = MockProcess(expected_command, expected_username)
        remote_processes = [MockProcess("123 sdf", expected_username), MockProcess(expected_command, "username"),
                            MockProcess("xxxx", "xxx"), expected_process]
        with mock.patch(self.REMOTE_TUNNEL_COMMAND_PROPERTY, expected_command):
            with mock.patch(self.REMOTE_PROCESS_GET_LIST_METHOD, mock.Mock(return_value=remote_processes)):
                process = jump_tunnel._find_tunnel_process_on_jump()
        assert process == expected_process

    def test_tunnel_process_on_jump_no_process(self, jump_tunnel):
        expected_command = "abc"
        expected_username = jump_tunnel._username
        remote_processes = [MockProcess("123 sdf", expected_username), MockProcess(expected_command, "username"),
                            MockProcess("xxxx", "xxx")]
        with mock.patch(self.REMOTE_TUNNEL_COMMAND_PROPERTY, expected_command):
            with mock.patch(self.REMOTE_PROCESS_GET_LIST_METHOD, mock.Mock(return_value=remote_processes)):
                process = jump_tunnel._find_tunnel_process_on_jump()
        assert process is None

    def test_close(self, jump_tunnel):
        with mock.patch.object(jump_tunnel, "_find_tunnel_process_on_jump", mock.Mock(return_value=mock.Mock())) as mock_process:
            mock_process.return_value.kill = mock.Mock()
            with mock.patch(self.SIMPLE_TUNNEL_CLOSE, mock.Mock()) as mock_super_close:
                jump_tunnel.close()
        mock_process.return_value.kill.assert_called_with()
        mock_super_close.assert_called_with()

    def test_close_no_process_on_jump(self, jump_tunnel):
        with mock.patch.object(jump_tunnel, "_find_tunnel_process_on_jump", mock.Mock(return_value=None)):
            with mock.patch(self.SIMPLE_TUNNEL_CLOSE, mock.Mock()) as mock_super_close:
                jump_tunnel.close()
        mock_super_close.assert_called_with()
