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

import copy
import os
from unittest import mock

import pytest

from modules.ssh_lib._remote_process import RemoteProcess


class TestRemoteProcess:
    PS_AUX_OUT_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "ps_aux_out")
    TEST_USER = "test"
    TEST_PID = 12345
    TEST_COMMAND = "test command -xyz 1234"
    TEST_HEADER = "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"

    @pytest.fixture(scope="class")
    def ps_aux_output(self):
        with open(self.PS_AUX_OUT_PATH) as f:
            return f.read().split("\n")

    @pytest.fixture(scope="class")
    def test_line(self, ps_aux_output):
        line = next((l for l in ps_aux_output if self.TEST_USER in l), None)
        assert line is not None
        assert str(self.TEST_PID) in line
        assert self.TEST_COMMAND in line
        return line

    @pytest.fixture(scope="function")
    def mock_ssh_client(self, ps_aux_output):
        class MockClient:
            ssh = mock.Mock(return_value=ps_aux_output)
        return MockClient()

    def test_init(self, mock_ssh_client):
        test_process = RemoteProcess(ssh_client=mock_ssh_client, user=self.TEST_USER, pid=self.TEST_PID,
                                     command=self.TEST_COMMAND)
        assert test_process._ssh_client == mock_ssh_client
        assert test_process.user == self.TEST_USER
        assert test_process.pid == self.TEST_PID
        assert test_process.command == self.TEST_COMMAND

    def test_init_incorrect_client_object(self):
        with pytest.raises(TypeError) as e:
            RemoteProcess(ssh_client=object(), user="a", pid=123, command="c")
        assert "does not have attribute ssh" in e.value.args[0]

    def test_get_list(self, mock_ssh_client):
        processes = RemoteProcess.get_list(mock_ssh_client)
        test_process = next((p for p in processes if p.user == self.TEST_USER), None)
        assert test_process is not None
        assert test_process._ssh_client == mock_ssh_client
        assert test_process.pid == self.TEST_PID
        assert test_process.command == self.TEST_COMMAND

    def test_get_list_no_header(self, ps_aux_output, mock_ssh_client):
        mock_ssh_client.ssh.return_value = ps_aux_output[1:]
        with pytest.raises(AssertionError) as e:
            RemoteProcess.get_list(mock_ssh_client)
        assert "There seems to be no header in output" in e.value.msg

    @pytest.mark.parametrize("tested_method,expected_value",
                             [(RemoteProcess._get_user_from_line, TEST_USER),
                              (RemoteProcess._get_pid_from_line, TEST_PID),
                              (RemoteProcess._get_command_from_line, TEST_COMMAND)])
    def test_get_from_line(self, ps_aux_output, test_line, tested_method, expected_value):
        item = tested_method(test_line, header=ps_aux_output[0])
        assert item == expected_value

    @pytest.mark.parametrize("invalid_line", ("", " ", "\n"))
    def test_get_user_from_line_no_user(self, ps_aux_output, invalid_line):
        with pytest.raises(AssertionError) as e:
            RemoteProcess._get_user_from_line(invalid_line, header=ps_aux_output[0])
        assert "Did not find process user" in e.value.msg

    @pytest.mark.parametrize("invalid_line", ("", " ", "\n"))
    def test_get_pid_from_line_no_pid(self, ps_aux_output, invalid_line):
        with pytest.raises(AssertionError) as e:
            RemoteProcess._get_pid_from_line(invalid_line, header=ps_aux_output[0])
        assert "Did not find process PID" in e.value.msg

    def test_get_pid_not_int(self, ps_aux_output, test_line):
        invalid_line = test_line.replace(str(self.TEST_PID), "abcde")
        with pytest.raises(ValueError) as e:
            RemoteProcess._get_pid_from_line(invalid_line, header=ps_aux_output[0])
        assert "Did not find process PID" in e.value.args[0]

    def test_kill(self, mock_ssh_client):
        test_process = RemoteProcess(ssh_client=mock_ssh_client, user=self.TEST_USER, pid=self.TEST_PID,
                                     command=self.TEST_COMMAND)
        test_process.kill()
        kill_command = "kill {}".format(test_process.pid)
        mock_ssh_client.ssh.assert_called_with(kill_command)

    @pytest.mark.parametrize("expected_index", (0, 20, -1))
    def test_find_header(self, ps_aux_output, expected_index):
        output_without_header = ps_aux_output[1:]
        test_output = copy.copy(output_without_header)
        test_output[expected_index] = self.TEST_HEADER
        index = RemoteProcess._find_header_index_in_ps_aux_output(test_output)
        assert index == test_output.index(self.TEST_HEADER)

    @pytest.fixture()
    def output_without_header(self, ps_aux_output):
        return {
            "no_header": ps_aux_output[1:],
            "empty_list": []
        }

    @pytest.mark.parametrize("test_case_name", ("no_header", "empty_list"))
    def test_find_header_no_header(self, output_without_header, test_case_name):
        with pytest.raises(AssertionError) as e:
            test_output = output_without_header[test_case_name]
            RemoteProcess._find_header_index_in_ps_aux_output(test_output)
        assert "There seems to be no header in output" in e.value.msg