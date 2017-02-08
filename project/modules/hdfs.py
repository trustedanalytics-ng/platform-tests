#
# Copyright (c) 2016-2017 Intel Corporation
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

import random
import string
import config
from modules.ssh_lib.jump_client import JumpClient
from modules.tap_logger import get_logger

logger = get_logger(__name__)


class Hdfs(object):
    _SSH = ["ssh", "-tt", "-o StrictHostKeyChecking=no"]
    _SUDO = ["sudo", "-u", "hdfs"]
    _HADOOP_CMD = ["dfs", "-ls"]
    _HADOOP_CMD_PERMISSION = ["dfs", "-getfacl"]
    _HDFS_CMD = _SUDO + ["hdfs"]
    _HADOOP_FS = ["hadoop", "fs"]

    def __init__(self, org: str):
        self.ssh_client = JumpClient(remote_host=config.jumpbox_hostname, remote_username=config.ng_jump_user,
                                     remote_key_path=config.jumpbox_key_path)
        self._HDFS_DIR = "/org/{}/brokers/userspace".format(org.guid)
        self.cdh_master_primary = self.get_cdhmaster()

    def _execute(self, command: list):
        jump = JumpClient(remote_host=config.jumpbox_hostname, remote_username=config.ng_jump_user,
                          remote_key_path=config.jumpbox_key_path)
        return jump.execute_ssh_command(self._SSH + [self.cdh_master_primary] + command)

    def ls(self, service_instance_id):
        directory_path = "{}/{}".format(self._HDFS_DIR, service_instance_id)
        return self._execute(self._SUDO + self._HADOOP_FS + ["-ls", directory_path])

    def cat(self, service_instance_id: str, file_name: str):
        path = "{}/{}/{}".format(self._HDFS_DIR, service_instance_id, file_name)
        return self._execute(self._SUDO + self._HADOOP_FS + ["-cat", path])

    def put(self, file_path, service_instance_id: str):
        path = "{}/{}".format(self._HDFS_DIR, service_instance_id)
        put = self._SUDO + self._HADOOP_FS + ["-put", "/tmp/{}".format(file_path), path]
        self._execute(put)

    def create_sample_file(self):
        content = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        file_name = "{}.txt".format(content[0:10])
        self.ssh_client.execute_ssh_command(["touch", file_name])
        fill_file = ["echo", "\"{}\"".format(content), ">>", file_name]
        self.ssh_client.execute_ssh_command(fill_file)
        self.ssh_client.execute_ssh_command(["scp", file_name, "{}:/tmp".format(self.cdh_master_primary)])
        self.ssh_client.execute_ssh_command(["rm", file_name])
        file = {'name': file_name, 'content': content}
        return file

    def list_zones(self):
        return self._execute(self._HDFS_CMD + ["crypto", "-listZones"])

    def get_cdhmaster(self):
        inventory = ["cat", "tap.inventory.out"]
        try:
            output = self.ssh_client.execute_ssh_command(inventory)
        except:
            output = self.ssh_client.execute_ssh_command(["ls"])
            TAP = next((s for s in output if 'configuration' in s), None)
            inventory = ["cat", "{}/tap.inventory.out".format(TAP)]
            output = self.ssh_client.execute_ssh_command(inventory)
        index = output.index('[cdh-master-primary]')
        cdh = output[index+1].split(" ")
        return cdh[0]

    def check_plain_dir_directory(self, service_instance_id: str):
        self._HADOOP_CMD.append(self._HDFS_DIR)
        command = self._HDFS_CMD + self._HADOOP_CMD
        out= self._execute(command)
        assert service_instance_id in str(out)

    def check_plain_dir_permissions(self, service_instance_id: str):
        permissions = ["user::rwx", "owner: broker", "group::rwx", "other::---"]
        directory = '{}{}{}'.format(self._HDFS_DIR, '/', service_instance_id)
        self._HADOOP_CMD_PERMISSION.append(directory)
        command = self._HDFS_CMD + self._HADOOP_CMD_PERMISSION
        out = self._execute(command)
        for item in permissions:
            assert item in str(out)
