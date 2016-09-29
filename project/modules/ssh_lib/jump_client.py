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
import shutil
import stat
import subprocess

from retry import retry

import config
from modules.app_sources import AppSources
import modules.command as cli_command
from modules.constants import TapGitHub, RelativeRepositoryPaths
from modules.tap_logger import get_logger


class JumpClient(object):
    _SSH_RETRY_DELAY = 30
    _SSH_RETRIES = 5
    _logger = get_logger(__name__)

    def __init__(self, username):
        self._username = username
        self._host = config.ng_jump_ip
        assert self._host is not None, "Missing jumpbox hostname configuration"
        self._ilab_deploy_path = None
        self._key_path = config.ng_jump_key_path
        self.auth_options = ["-o UserKnownHostsFile=/dev/null",
                             "-o StrictHostKeyChecking=no",
                             "-o GSSAPIAuthentication=no"]
        ssh_options = ["-i", self.key_path] + self.auth_options + ["{}@{}".format(self._username, self._host)]
        scp_options = ["-r", "-i", self.key_path] + self.auth_options
        if config.verbose_ssh:
            ssh_options = ["-vvv"] + ssh_options
            scp_options = ["-v"] + scp_options
        self.ssh_command = ["ssh"] + ssh_options
        self.scp_command = ["scp"] + scp_options

    @property
    def key_path(self):
        """
        If key path was not set in configuration, download key.
        Download is executed at most once.
        """
        if self._key_path is None:
            self._logger.info("Download repository with ssh key")
            ilab_deploy = AppSources.get_repository(repo_name=TapGitHub.ilab_deploy, repo_owner=TapGitHub.intel_data)
            self._ilab_deploy_path = ilab_deploy.path
            self._key_path = os.path.join(self._ilab_deploy_path, RelativeRepositoryPaths.ilab_jump_key)
            os.chmod(self._key_path, stat.S_IRUSR | stat.S_IWUSR)
        self._key_path = os.path.expanduser(self._key_path)
        assert os.path.isfile(self._key_path), "No such file {}".format(self._key_path)
        return self._key_path

    def ssh(self, remote_command):
        if not isinstance(remote_command, list):
            remote_command = [remote_command]
        command = self.ssh_command + remote_command
        return cli_command.run(command)

    def scp_from_remote(self, source_path, target_path):
        command = self.scp_command + ["{}@{}:{}".format(self._username, self._host, source_path), target_path]
        self._run_command(command)

    def scp_to_remote(self, source_path, target_path):
        command = self.scp_command + [source_path, "{}@{}:{}".format(self._username, self._host, target_path)]
        self._run_command(command)

    def cleanup(self):
        if self._ilab_deploy_path is not None and os.path.exists(self._ilab_deploy_path):
            self._logger.debug("Remove directory {}".format(self._ilab_deploy_path))
            shutil.rmtree(self._ilab_deploy_path)

    def _run_command(self, command):
        self._logger.info("Executing command {}".format(" ".join(command)))
        process = subprocess.Popen(command)
        try:
            self._logger.info("Wait for command {} to finish".format(" ".join(command)))
            self._ensure_process_finished(process, command)
        except subprocess.TimeoutExpired:
            self._logger.info("Killing {}".format(" ".join(command)))
            process.kill()
            raise

    @retry(subprocess.TimeoutExpired, tries=_SSH_RETRIES, delay=_SSH_RETRY_DELAY)
    def _ensure_process_finished(self, process, command):
        if process.poll() is None:
            raise subprocess.TimeoutExpired(command, self._SSH_RETRY_DELAY)
