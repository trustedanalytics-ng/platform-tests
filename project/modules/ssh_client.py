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
from datetime import datetime
import os
import subprocess

import paramiko
import sshtunnel

from modules.command import run
from modules.exceptions import CommandExecutionException
from modules.remote_logger.config import Config
from modules.tap_logger import log_command, get_logger


logger = get_logger(__name__)


SSH_POLICY = paramiko.AutoAddPolicy()
EXIT_STATUS_OK = 0


class SshConfig:

    JUMPBOX_USERNAME = "ubuntu"
    CDH_MASTER_0_HOSTNAME = "cdh-master-0"
    CDH_MASTER_2_HOSTNAME = "cdh-master-2"
    CDH_MASTER_USERNAME = "ec2-user"
    CLOUDERA_MANAGER_PORT = 7180


class RemoteCommand(object):
    """Remember to use .decode() on stdout/stderr output file-like objects."""

    def __init__(self, command: str, channel: paramiko.channel.Channel, stdin: paramiko.channel.ChannelFile,
                 stdout: paramiko.channel.ChannelFile, stderr: paramiko.channel.ChannelFile):
        self.command = command
        self.channel = channel
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def get_return_code(self):
        """Return exit status of the process, wait if necessary."""
        return self.channel.recv_exit_status()

    def assert_return_code_ok(self):
        status = self.get_return_code()
        if status != EXIT_STATUS_OK:
            msg = "Wrong status code {} of command {}".format(status, self.command)
            logger.error("%s, stdout: %s, stderr: %s", msg, self.get_stdout_as_str(), self.get_stderr_as_str())
            raise CommandExecutionException(msg)

    def get_stdout_as_str(self):
        return self.stdout.read().decode()

    def get_stderr_as_str(self):
        return self.stderr.read().decode()


class DirectSshClient(object):
    def __init__(self, hostname, username, port=22, path_to_key=None):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.path_to_key = path_to_key
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(SSH_POLICY)

    def connect(self):
        self.client.connect(self.hostname, port=self.port, username=self.username, key_filename=self.path_to_key)

    def disconnect(self):
        self.client.close()

    def exec_command(self, command):
        log_command(command)
        command = " ".join(command)
        _, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()


class NestedSshClient(object):
    def __init__(self, hostname, username, path_to_key=None, port=22, via_hostname=None, via_username=None,
                 via_path_to_key=None, via_port=22, local_port=1234):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.path_to_key = path_to_key
        self.via_hostname = via_hostname
        self.via_username = via_username
        self.via_path_to_key = via_path_to_key
        self.via_port = via_port
        self.local_port = local_port
        if self.via_username is None:
            self.via_username = self.username
        if self.via_path_to_key is None:
            self.via_path_to_key = self.path_to_key
        self.proxy = paramiko.SSHClient()
        self.proxy.set_missing_host_key_policy(SSH_POLICY)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(SSH_POLICY)

    def connect(self):
        self.proxy.connect(self.via_hostname, port=self.via_port, username=self.via_username,
                           key_filename=self.via_path_to_key)
        proxy_transport = self.proxy.get_transport()
        channel = proxy_transport.open_channel("direct-tcpip", dest_addr=(self.hostname, self.port),
                                               src_addr=("localhost", self.local_port))
        self.client.connect("localhost", port=self.local_port, username=self.username, sock=channel,
                            key_filename=self.path_to_key)

    def disconnect(self):
        self.proxy.close()
        self.client.close()

    def exec_command_non_interactive(self, command):
        ssh_cmd = self.exec_command_interactive(command)
        return (
            ssh_cmd.get_return_code(),
            ssh_cmd.get_stdout_as_str(),
            ssh_cmd.get_stderr_as_str()
        )

    def exec_command_interactive(self, command):
        log_command(command)
        command = " ".join(command)
        channel = self.client.get_transport().open_session()
        channel.exec_command(command)
        return RemoteCommand(
            command,
            channel,
            channel.makefile('wb', -1),
            channel.makefile('r', -1),
            channel.makefile_stderr('r', -1)
        )


class SshTunnel(object):
    def __init__(self, hostname, username, path_to_key=None, port=22, via_hostname=None, via_port=22, local_port=1234):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.path_to_key = path_to_key
        self.via_hostname = via_hostname
        self.via_port = via_port
        self.local_port = local_port
        ssh_address = (self.via_hostname, self.via_port)
        ssh_private_key = os.path.expanduser(self.path_to_key)
        ssh_private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key)
        local_bind_address = ("localhost", self.local_port)
        remote_bind_address = (self.hostname, self.port)
        self.client = sshtunnel.SSHTunnelForwarder(ssh_address=ssh_address, ssh_username=self.username,
                                                   ssh_private_key=ssh_private_key, local_bind_address=local_bind_address,
                                                   remote_bind_address=remote_bind_address)

    def connect(self):
        self.client.start()

    def disconnect(self):
        self.client.stop()


class SshTunnelException(Exception):
    pass


class ClouderManagerSshTunnel(SshTunnel):

    def __init__(self):
        super().__init__(
            hostname=SshConfig.CDH_MASTER_2_HOSTNAME,
            username=SshConfig.JUMPBOX_USERNAME,
            path_to_key=Config.get_cdh_key_path(),
            port=SshConfig.CLOUDERA_MANAGER_PORT,
            via_hostname=Config.get_jumpbox_host_address()
        )


class CdhMasterClient:

    def __init__(self, cdh_host_name):
        self.cdh_host_name = cdh_host_name
        self.output_path = "/tmp/{}".format(datetime.now().strftime("%Y%m%d_%H%M%S_%f"))

        ssh_no_host_checking = ["-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no"]
        key_path = Config.get_cdh_key_path()
        jumpbox_host = Config.get_jumpbox_host_address()

        self._prepare_commands = [["set", "-e"], ["rm", "-rf", self.output_path], ["mkdir", self.output_path]]
        self._ssh_command = ["ssh", "-tt"] + ssh_no_host_checking + ["-i", key_path,
                                                                     "{}@{}".format(SshConfig.JUMPBOX_USERNAME,
                                                                                    jumpbox_host),
                                                                     "sudo", "ssh",
                                                                     "-tt"] + ssh_no_host_checking + \
                            ["{}@{}".format(SshConfig.CDH_MASTER_USERNAME, self.cdh_host_name)]
        self._rsync_command = [
            "rsync", "-avz", "--delete", "-e", "ssh {}@{} {} -i {} sudo ssh {}".format(
                SshConfig.JUMPBOX_USERNAME, jumpbox_host,
                " ".join(ssh_no_host_checking),
                key_path, " ".join(ssh_no_host_checking)),
            "{}@{}:{}/".format(SshConfig.CDH_MASTER_USERNAME, self.cdh_host_name, self.output_path), self.output_path
        ]

    def exec_commands(self, commands):
        """
        :param commands: list of commands
        :return: list with std commands outputs (out and err)

        Example:
            exec_commands([["echo", "hello"], ["python", "-c", "import os; os.write(2, \"world\")"]])
            -> [["hello", ""], ["", "world"]]
        """
        process = subprocess.Popen(self._ssh_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, universal_newlines=True)

        string_commands = self._send_commands_to_process(process, commands)

        while True:
            output = process.stdout.readline().strip()
            if output == '' and process.poll() is not None:
                break
            if output != '':
                logger.info(output)

        outputs = self._get_commands_outputs(string_commands)

        return_code = process.poll()
        if return_code != 0:
            raise CommandExecutionException(return_code, " ".join(self._ssh_command))

        return outputs

    @classmethod
    def _ensure_quote(cls, query):
        query = query.strip()
        if query[0] not in "'\"":
            query = "'{}'".format(query)
        return query

    def _send_commands_to_process(self, process, commands):
        for command in self._prepare_commands:
            process.stdin.write(" ".join(command + ["\n"]))

        string_commands = []

        for i, command in enumerate(commands):
            command = [self._ensure_quote(i) for i in command]
            string_command = " ".join(
                command + ["1>{}/{}_1".format(self.output_path, i), "2>{}/{}_2".format(self.output_path, i), "\n"])
            logger.info("Executing command: %s", string_command)
            process.stdin.write(string_command)
            string_commands.append(string_command)
        process.stdin.write("exit 0\n")
        process.stdin.close()

        return string_commands

    def _get_commands_outputs(self, string_commands):
        run(self._rsync_command)

        cmds_outputs = []
        for i, command in enumerate(string_commands):
            logger.info("Outputs from command: %s", command)
            cmd_outputs = []
            for fd_name, fd in [("stdout", 1), ("stderr", 2)]:
                logger.info("%s:", fd_name)
                path = "{}/{}_{}".format(self.output_path, i, fd)
                if os.path.exists(path):
                    with open(path) as f:
                        output = f.read().strip()
                else:
                    raise CommandExecutionException("No {} output of command {}".format(fd_name, command))
                cmd_outputs.append(output)
                logger.info(output)
            cmds_outputs.append(cmd_outputs)

        return cmds_outputs
