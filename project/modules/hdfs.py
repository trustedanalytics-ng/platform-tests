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

from .exceptions import HdfsException
from .ssh_client import CdhMasterSshClient
from .tap_logger import get_logger


logger = get_logger(__name__)


class Hdfs(object):

    def __init__(self):
        self.ssh_client = CdhMasterSshClient()
        self.ssh_client.connect()
        logger.info("Accessing HDFS on {} via {}".format(self.ssh_client.hostname, self.ssh_client.via_hostname))
        self.hadoop_fs = ["hadoop", "fs"]

    def _execute(self, command):
        _, stdout, stderr = self.ssh_client.exec_command_non_interactive(command)
        if stderr != "":
            raise HdfsException(stderr)
        return stdout

    def ls(self, directory_path):
        """Execute ls on a directory in hdfs. Return a list of file paths."""
        command = self.hadoop_fs + ["-ls", directory_path]
        output = self._execute(command)
        paths = []
        for line in [line for line in output.split("\n")[1:-1]]:
            r = re.search("\/.*$", line)
            paths.append(line[r.start():r.end()])
        return paths

    def cat(self, file_path):
        command = self.hadoop_fs + ["-cat", file_path]
        output = self._execute(command)
        return output





