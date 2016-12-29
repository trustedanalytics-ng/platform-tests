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

import re
import config
from modules.ssh_lib.jump_client import JumpClient
from modules.tap_logger import get_logger

logger = get_logger(__name__)


class Hdfs(object):
    _SSH = ["ssh", "-tt"]
    _SUDO = ["sudo", "-u", "hdfs"]
    _HADOOP_CMD = ["dfs", "-ls"]
    _HADOOP_CMD_PERMISSION = ["dfs", "-getfacl"]
    _HDFS_CMD = _SUDO + ["hdfs"]
    _PUT = ["hadoop", "fs"]

    def __init__(self, org: str):
        self.ssh_client = JumpClient(remote_host=config.jumpbox_hostname, remote_username=config.ng_jump_user,
                                     remote_key_path=config.jumpbox_key_path)
        self._PLAIN_DIR = "/org/{}/brokers/userspace".format(org.guid)
        cdh_master_primary = self.get_cdhmaster()
        self._SSH.append(cdh_master_primary)

    def _execute(self, command: list):
        jump = JumpClient(remote_host=config.jumpbox_hostname, remote_username=config.ng_jump_user,
                          remote_key_path=config.jumpbox_key_path)
        return jump.execute_ssh_command(self._SSH + command)

    def ls(self, directory_path):
        """Execute ls on a directory in hdfs. Return a list of file paths."""
        output = self._execute(self._HADOOP_CMD + ["-ls", directory_path])
        paths = []
        for line in [line for line in output.split("\n")[1:-1]]:
            r = re.search(r"/.*$", line)
            paths.append(line[r.start():r.end()])
        return paths

    def cat(self, file_path):
        return self._execute(self._HADOOP_CMD + ["-cat", file_path])

    def put(self, file_path, content):
        tmp_path = "/tmp/test_file"
        self._execute(["python", "-c",
                       "import sys;open(\"{}\",\"w\").write(sys.argv[1])".format(tmp_path),
                       content])
        self._execute(self._HADOOP_CMD + ["-put", tmp_path, file_path])

    def list_zones(self):
        return self._execute(self._HDFS_CMD + ["crypto", "-listZones"])

    def get_cdhmaster(self):
        k8s = ["cat", "k8s"]
        output = self.ssh_client.execute_ssh_command(k8s)
        index = output.index('[cdh-master-primary]')
        cdh = output[index+1].split(" ")
        return cdh[0]

    def check_plain_dir_directory(self, service_instance_id: str):
        self._HADOOP_CMD.append(self._PLAIN_DIR)
        command = self._HDFS_CMD + self._HADOOP_CMD
        out= self._execute(command)
        assert service_instance_id in str(out)

    def check_plain_dir_permissions(self, service_instance_id: str):
        permissions = ["user::rwx", "owner: broker", "group::rwx", "other::---"]
        directory = '{}{}{}'.format(self._PLAIN_DIR, '/', service_instance_id)
        self._HADOOP_CMD_PERMISSION.append(directory)
        command = self._HDFS_CMD + self._HADOOP_CMD_PERMISSION
        out = self._execute(command)
        for item in permissions:
            assert item in str(out)
