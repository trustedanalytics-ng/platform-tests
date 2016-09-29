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

from unittest import mock

import pytest

from ._mocks import MockConfig
from modules.ssh_lib._simple_jump_tunnel import SimpleJumpTunnel


@mock.patch("modules.ssh_lib._jump_client.config", MockConfig())
class TestSimpleJumpTunnel:
    CONFIG_MODULE = "modules.ssh_lib._simple_jump_tunnel.config"
    CLIENT_GET_REPOSITORY = "modules.ssh_lib._jump_client.AppSources.get_repository"
    JUMP_CLIENT_CLASS = "modules.ssh_lib._simple_jump_tunnel.JumpClient"
    SUBPROCESS_POPEN_CLASS = "modules.ssh_lib._simple_jump_tunnel.subprocess.Popen"
    CHECK_TUNNEL_ESTABLISHED = "modules.ssh_lib._simple_jump_tunnel.SimpleJumpTunnel._check_tunnel_established"
    CLOSE = "modules.ssh_lib._simple_jump_tunnel.SimpleJumpTunnel.close"

    MOCK_SSH_COMMAND = ["mock", "ssh", "command"]

    def test_init(self):
        with mock.patch(self.CONFIG_MODULE, MockConfig()) as mock_config:
            with mock.patch(self.JUMP_CLIENT_CLASS) as mock_client:
                mock_instance = mock_client.return_value
                mock_instance.ssh_command = self.MOCK_SSH_COMMAND
                jump_tunnel = SimpleJumpTunnel()
        mock_client.assert_called_with(mock_config.ng_jump_user)
        assert jump_tunnel._local_port == mock_config.ng_socks_proxy_port
        assert " ".join(mock_instance.ssh_command) in " ".join(jump_tunnel._tunnel_command)
        assert "-D {}".format(mock_config.ng_socks_proxy_port) in " ".join(jump_tunnel._tunnel_command)
        assert jump_tunnel._tunnel is None

    @pytest.fixture(scope="function")
    @mock.patch(CONFIG_MODULE, MockConfig())
    def jump_tunnel(self):
        with mock.patch(self.JUMP_CLIENT_CLASS) as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.ssh_command = self.MOCK_SSH_COMMAND
            return SimpleJumpTunnel()

    @mock.patch(CHECK_TUNNEL_ESTABLISHED, mock.Mock())
    def test_open_success(self, jump_tunnel):
        test_subprocess = "test"
        with mock.patch(self.SUBPROCESS_POPEN_CLASS, mock.Mock(return_value=test_subprocess)):
            jump_tunnel.open()
        assert jump_tunnel._tunnel == test_subprocess

    @mock.patch(SUBPROCESS_POPEN_CLASS, mock.Mock())
    @mock.patch(CHECK_TUNNEL_ESTABLISHED, mock.Mock(side_effect=Exception()))
    def test_open_exception(self, jump_tunnel):
        with mock.patch(self.CLOSE) as mock_close:
            with pytest.raises(Exception):
                jump_tunnel.open()
        mock_close.assert_called_once()

