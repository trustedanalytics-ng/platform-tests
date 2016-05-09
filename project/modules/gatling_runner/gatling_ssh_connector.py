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
from time import sleep

import paramiko

from modules.constants import LoggerType
from modules.tap_logger import get_logger
from .config import Config
from .gatling_runner_parameters import GatlingRunnerParameters

logger = get_logger(LoggerType.GATLING_RUNNER)


class GatlingSshConnector(object):
    """Gatling remote host ssh connector."""

    SSH_POLICY = paramiko.AutoAddPolicy()
    PATH_TO_LOG_FILE = "simulation.log"
    PATH_TO_RESULT_FILE = os.path.join("js", "global_stats.json")
    PATH_TO_RESULTS = "results"
    WAIT_AFTER_SIMULATION_START = 2  # in seconds

    def __init__(self, parameters: GatlingRunnerParameters):
        self._parameters = parameters
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(self.SSH_POLICY)
        self._connect()
        self._prepare_root_directory()

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.close()

    def close(self):
        """Close remote host connection."""
        self._client.close()

    def start_simulation(self):
        """Start simulation with parameters as background process."""
        self._prepare_package()
        sftp = self._open_sftp()
        sftp.chdir(self.PATH_TO_RESULTS)
        folders_before = sftp.listdir()
        self._exec_command(self._command())
        sleep(self.WAIT_AFTER_SIMULATION_START)
        folders_after = sftp.listdir()
        sftp.close()
        execution_directory = self._get_execution_directory(folders_after, folders_before)
        logger.info('Execution directory: "{}"'.format(execution_directory))
        return execution_directory

    def get_log_size(self) -> int:
        """Return simulation log file size."""
        return self._get_file_size(self._simulation_path(self.PATH_TO_LOG_FILE))

    def is_results_ready(self) -> bool:
        """Check if there is json file with results."""
        file_size = self._get_file_size(self._simulation_path(self.PATH_TO_RESULT_FILE))
        return file_size > 0

    def get_results(self) -> str:
        """Get gatling results json file as string."""
        sftp = self._open_sftp()
        try:
            with sftp.open(self._simulation_path(self.PATH_TO_RESULT_FILE), "r") as f:
                results = f.read().decode()
        finally:
            sftp.close()
        return results

    def _simulation_path(self, file_path):
        """Return path to file based on simulation directory."""
        return os.path.join(self.PATH_TO_RESULTS, self._parameters.execution_directory, file_path)

    def _prepare_package(self):
        """Upload gatling package if not exists."""
        if self._get_file_size(Config.gatling_package_file_name()) == 0:
            logger.info('Uploading package: "{}"'.format(Config.gatling_package_file_name()))
            sftp = self._open_sftp()
            try:
                sftp.put(Config.gatling_package_file_path(), Config.gatling_package_file_name())
            finally:
                sftp.close()

    def _command(self):
        """Simulation execution command."""
        command = [
            'java',
            '-Dsimulation={}'.format(self._parameters.simulation_name.value),
            '-Dplatform={}'.format(self._parameters.platform),
            '-Dusername={}'.format(self._parameters.username),
            '-Dpassword={}'.format(self._parameters.password),
            '-Dorganization={}'.format(self._parameters.organization),
            '-Dspace={}'.format(self._parameters.space),
            '-Dusers={}'.format(self._parameters.users),
            '-DusersAtOnce={}'.format(self._parameters.users_at_once),
            '-Dramp={}'.format(self._parameters.ramp),
            '-Drepeat={}'.format(self._parameters.repeat),
            '-Dduration={}'.format(self._parameters.duration),
        ]
        if self._parameters.proxy is not None:
            command.extend([
                '-Dproxy={}'.format(self._parameters.proxy),
                '-DproxyHttpPort={}'.format(self._parameters.proxy_http_port),
                '-DproxyHttpsPort={}'.format(self._parameters.proxy_https_port),
            ])
        command.extend([
            '-jar', Config.gatling_package_file_name(),
            '>', self._parameters.log_file, '2>&1', '&'
        ])
        return command

    def _exec_command(self, command_items):
        """Execute remote command."""
        command = " ".join(command_items)
        logger.info('Executing command: "{}"'.format(command))
        std_in, std_out, std_err = self._client.exec_command("cd {}; {}".format(Config.gatling_repo_name(), command))
        if std_out.channel.recv_exit_status() > 0:
            raise GatlingSshConnectorExecuteCommandException(std_err.read().decode())
        return std_out.readlines()

    def _get_file_size(self, path):
        """Return remote file size."""
        sftp = self._open_sftp()
        try:
            file_attributes = sftp.lstat(path)
            file_size = file_attributes.st_size
        except FileNotFoundError:
            file_size = 0
        finally:
            sftp.close()
        return file_size

    def _open_sftp(self):
        """Create SFTP client."""
        sftp = self._client.open_sftp()
        sftp.chdir(Config.gatling_repo_name())
        return sftp

    def _connect(self):
        """Connect to gatling remote host."""
        try:
            self._client.connect(
                Config.gatling_ssh_host(),
                port=Config.gatling_ssh_port(),
                username=Config.gatling_ssh_username(),
                key_filename=Config.gatling_ssh_key_path()
            )
        except paramiko.SSHException:
            raise GatlingSshConnectorException

    def _prepare_root_directory(self):
        """Prepare gatling tests root directory."""
        target_path = os.path.join(Config.gatling_repo_name(), "target", "test-classes")
        self._client.exec_command("mkdir -p {}".format(target_path))
        results_path = os.path.join(Config.gatling_repo_name(), self.PATH_TO_RESULTS)
        self._client.exec_command("mkdir -p {}".format(results_path))

    @staticmethod
    def _get_execution_directory(folders_after, folders_before):
        folders_diff = list(set(folders_after) - set(folders_before))
        if not folders_diff:
            raise GatlingSshConnectorExecuteCommandException
        return folders_diff[0]


class GatlingSshConnectorException(Exception):
    def __init__(self):
        super().__init__("Gatling connector ssh connection problem.")


class GatlingSshConnectorExecuteCommandException(Exception):
    pass
