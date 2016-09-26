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

from ._mocks import MockConfig, MockSystemMethods
from modules.ssh_lib.jump_tunnel import JumpClient, JumpTunnel


jump_client_mock_config = MockConfig()


@mock.patch("modules.ssh_lib.jump_client.os.path.isfile", MockSystemMethods.isfile)
@mock.patch("modules.ssh_lib.jump_client.os.path.exists", MockSystemMethods.exists)
@mock.patch("modules.ssh_lib.jump_client.config", jump_client_mock_config)
class TestJumpTunnel:
    CONFIG_MODULE = "modules.ssh_lib.jump_tunnel.config"
    COPY_KEY_METHOD = "modules.ssh_lib.jump_tunnel.JumpTunnel._copy_key_to_remote_host"

    @pytest.mark.parametrize("simple_ssh", (True, False))
    def test_init_simple_ssh(self, simple_ssh):
        with mock.patch(self.CONFIG_MODULE, MockConfig(direct_access_from_jump=simple_ssh)) as mock_config:
            with mock.patch(self.COPY_KEY_METHOD, mock.Mock()) as mock_copy_key_method:
                jump_tunnel = JumpTunnel()
        assert jump_tunnel._username == mock_config.ng_jump_user
        assert isinstance(jump_tunnel._jump_client, JumpClient)
        assert jump_tunnel._jump_client._username == jump_tunnel._username
        assert jump_tunnel._ssh_command == jump_tunnel._jump_client.ssh_command
        assert jump_tunnel._auth_options == jump_tunnel._jump_client.auth_options
        assert jump_tunnel._key_path == mock_config.ng_jump_key_path
        assert jump_tunnel._local_port == mock_config.ng_socks_proxy_port
        assert jump_tunnel._master_0_host == mock_config.master_0_hostname
        assert jump_tunnel._home_directory == "/home/{}".format(mock_config.ng_jump_user)
        assert jump_tunnel._tunnel is None

        if simple_ssh:
            assert "-D {}".format(mock_config.ng_socks_proxy_port) in " ".join(jump_tunnel._tunnel_command)
            mock_copy_key_method.assert_not_called()
        else:
            assert "-L" in jump_tunnel._tunnel_command
            assert "{0}:{1}:{0}".format(mock_config.ng_socks_proxy_port, JumpTunnel._LOCALHOST) in jump_tunnel._tunnel_command
            mock_copy_key_method.assert_called_once()
