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
from modules.exceptions import HdfsException
from modules.ssh_client import CdhMasterClient
from modules.tap_logger import get_logger

logger = get_logger(__name__)


class Hdfs(object):
    _SUDO = ["sudo", "-u", "hdfs"]
    _HADOOP_CMD = _SUDO + ["hadoop", "fs"]
    _HDFS_CMD = _SUDO + ["hdfs"]

    def __init__(self):
        self.ssh_client = CdhMasterClient(config.cdh_master_0_hostname)
        logger.info("Accessing HDFS on {}".format(self.ssh_client.cdh_host_name))

    def _execute(self, command):
        stdout, stderr = self.ssh_client.exec_commands([command])[0]
        if stderr != "":
            raise HdfsException(stderr)
        return stdout

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
