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


class RemoteProcess(object):
    PS_COMMAND = "ps aux"
    KILL_COMMAND = "kill {}"
    USER_HEADER = "USER"
    PID_HEADER = "PID"
    COMMAND_HEADER = "COMMAND"

    def __init__(self, ssh_client, user: str, pid: int, command: str):
        if not hasattr(ssh_client, "ssh"):
            raise TypeError("{} object does not have attribute ssh".format(type(ssh_client)))
        self._ssh_client = ssh_client
        self.user = user
        self.pid = pid
        self.command = command

    def __repr__(self):
        return "{} (user={}, pid={}, command={})".format(self.__class__.__name__, self.user, self.pid, self.command)

    @classmethod
    def get_list(cls, ssh_client):
        output = ssh_client.ssh(cls.PS_COMMAND)
        header_index = cls._find_header_index_in_ps_aux_output(output)
        header = output[header_index]
        processes = []
        for line in output[header_index+1:]:
            try:
                process = cls(ssh_client=ssh_client,
                              user=cls._get_user_from_line(line, header),
                              pid=cls._get_pid_from_line(line, header),
                              command=cls._get_command_from_line(line, header))
                processes.append(process)
            except:
                # Ignore parsing errors, command output is unpredictable
                continue
        return processes

    def kill(self):
        self._ssh_client.ssh(self.KILL_COMMAND.format(self.pid))

    @classmethod
    def _get_user_from_line(cls, line: str, header: str) -> str:
        index = header.index(cls.USER_HEADER)
        matches = re.findall(r"\S+", line[index:])
        assert len(matches) > 0, "Did not find process user in line '{}'".format(line)
        return matches[0]

    @classmethod
    def _get_pid_from_line(cls, line, header):
        end_index = header.index(cls.PID_HEADER) + len(cls.PID_HEADER)
        matches = re.findall(r"\S+", line[:end_index])
        assert len(matches) > 0, "Did not find process PID in line '{}'".format(line)
        try:
            pid = int(matches[-1], base=10)
        except ValueError:
            raise ValueError("Did not find process PID in line '{}".format(line))
        return pid

    @classmethod
    def _get_command_from_line(cls, line, header):
        """This method is implemented with the assumption that COMMAND is the last column."""
        index = header.index(cls.COMMAND_HEADER)
        return line[index:]

    @classmethod
    def _find_header_index_in_ps_aux_output(cls, output: list):
        for index, line in enumerate(output):
            if all(header in line for header in (cls.USER_HEADER, cls.PID_HEADER, cls.COMMAND_HEADER)):
                return index
        raise AssertionError("There seems to be no header in output of '{}'".format(cls.PS_COMMAND))

