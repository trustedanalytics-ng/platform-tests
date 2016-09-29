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
import stat
from unittest import mock

import pytest

from modules.ssh_lib.jump_client import JumpClient
from ._mocks import MockSystemMethods, MockConfig



@mock.patch("modules.ssh_lib.jump_client.os.path.isfile", MockSystemMethods.isfile)
@mock.patch("modules.ssh_lib.jump_client.os.path.exists", MockSystemMethods.exists)
class TestJumpClient:
    TEST_USERNAME = "test-username"
    CONFIG_MODULE = "modules.ssh_lib.jump_client.config"
    GET_REPOSITORY = "modules.ssh_lib.jump_client.AppSources.get_repository"
    RELATIVE_REPO_PATH = "modules.ssh_lib.jump_client.RelativeRepositoryPaths.ilab_jump_key"
    CHMOD = "modules.ssh_lib.jump_client.os.chmod"
    RMTREE = "modules.ssh_lib.jump_client.shutil.rmtree"

    @pytest.fixture()
    def dummy_object(self):
        class Dummy: pass
        return Dummy()

    @pytest.mark.parametrize("verbose_ssh", (False, True), ids=("verbose_ssh=False", "verbose_ssh=True"))
    def test_init(self, verbose_ssh):
        mock_config = MockConfig()
        with mock.patch(self.CONFIG_MODULE, MockConfig(verbose_ssh=verbose_ssh)):
            test_client = JumpClient(username=self.TEST_USERNAME)
        assert test_client._username == self.TEST_USERNAME
        assert test_client._host == mock_config.ng_jump_ip
        assert test_client._ilab_deploy_path is None
        assert test_client._key_path == mock_config.ng_jump_key_path
        assert test_client.key_path == test_client._key_path
        assert test_client.key_path in test_client.ssh_command
        assert test_client.key_path in test_client.scp_command
        assert " ".join(test_client.auth_options) in " ".join(test_client.ssh_command)
        assert " ".join(test_client.auth_options) in " ".join(test_client.scp_command)

        if verbose_ssh:
            assert "-vvv" in test_client.ssh_command
            assert "-v" in test_client.scp_command
        else:
            assert "-vvv" not in test_client.ssh_command
            assert "-v" not in test_client.scp_command

    @mock.patch(CONFIG_MODULE, MockConfig(jump_hostname=None))
    def test_no_jump_ip(self):
        with pytest.raises(AssertionError) as e:
            JumpClient(username=self.TEST_USERNAME)
        assert e.value.msg == "Missing jumpbox hostname configuration"

    @mock.patch(CONFIG_MODULE, MockConfig(jump_key_path="/i/dont/exist"))
    def test_key_path_not_existing_key(self):
        with pytest.raises(AssertionError) as e:
            JumpClient(username=self.TEST_USERNAME)
        assert "No such file" in e.value.msg

    def test_key_path_home_dir_expansion(self):
        mock_config = MockConfig(jump_key_path=MockConfig.JUMP_KEY_HOME_DIR)
        with mock.patch(self.CONFIG_MODULE, mock_config):
            test_client = JumpClient(username=self.TEST_USERNAME)
        assert test_client._key_path == os.path.expanduser(mock_config.ng_jump_key_path)
        assert test_client._key_path == test_client.key_path

    @mock.patch(RELATIVE_REPO_PATH, MockConfig.JUMP_KEY_FILENAME)
    @mock.patch(CONFIG_MODULE, MockConfig(jump_key_path=None))
    def test_download_key(self, dummy_object):
        dummy_object.path = MockConfig.JUMP_KEY_DIRECTORY
        with mock.patch(self.GET_REPOSITORY, mock.Mock(return_value=dummy_object)):
            with mock.patch(self.CHMOD, mock.Mock()) as mock_chmod:
                test_client = JumpClient(username=self.TEST_USERNAME)
        assert test_client._key_path == os.path.join(MockConfig.JUMP_KEY_DIRECTORY, MockConfig.JUMP_KEY_FILENAME)
        assert test_client.key_path == test_client._key_path
        assert test_client._ilab_deploy_path == dummy_object.path
        mock_chmod.assert_called_with(test_client._key_path, stat.S_IRUSR | stat.S_IWUSR)

    @mock.patch(RELATIVE_REPO_PATH, MockConfig.JUMP_KEY_FILENAME)
    @mock.patch(CONFIG_MODULE, MockConfig(jump_key_path=None))
    @mock.patch(CHMOD, lambda *args, **kwargs: None)
    def test_cleanup(self, dummy_object):
        dummy_object.path = MockConfig.JUMP_KEY_DIRECTORY
        with mock.patch(self.GET_REPOSITORY, mock.Mock(return_value=dummy_object)):
            test_client = JumpClient(username=self.TEST_USERNAME)
        with mock.patch(self.RMTREE, mock.Mock()) as mock_rmtree:
            test_client.cleanup()
        mock_rmtree.assert_called_with(dummy_object.path)

    def test_cleanup_no_directory_to_cleanup(self):
        mock_config = MockConfig()
        with mock.patch(self.CONFIG_MODULE, mock_config):
            test_client = JumpClient(username=self.TEST_USERNAME)
        with mock.patch(self.RMTREE, mock.Mock()) as mock_rmtree:
            test_client.cleanup()
        mock_rmtree.assert_not_called()
