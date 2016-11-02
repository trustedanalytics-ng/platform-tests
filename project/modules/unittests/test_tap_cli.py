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

import unittest
from unittest.mock import patch

import config
from modules.tap_cli import TapCli


class TestTapCli(unittest.TestCase):
    """Unit: TapCli."""
    assertion_errors = 0
    service_state = {
        "starting": {"state": "STARTING"},
        "running":  {"state": "RUNNING"},
        "failure": {"state": "FAILURE"}
    }
    gibberish_string = 'XphlIEv55DOEo6udmPim GSKu0b8GkK2z4pNb2J4w Aq0E5ZGegtEk0M65sA4d'

    def _run_command_get_service(self, cmd: list):
        return '{\n"name":"test1",\n"state":"RUNNING",\n"serviceName":"etcd",\n"planName":"free"\n}\n'

    def _run_command_get_service_command(self, cmd: list):
        assert ['service', 'test1'] == cmd
        return '{\n"name":"test1",\n"state":"RUNNING",\n"serviceName":"etcd",\n"planName":"free"\n}\n'

    def _run_command_get_service_short_command(self, cmd: list):
        assert ['s', 'test1'] == cmd
        return '{\n"name":"test1",\n"state":"RUNNING",\n"serviceName":"etcd",\n"planName":"free"\n}\n'

    def _run_command_get_wrong_service_name(self, cmd: list):
        return '{\n"name":"test2",\n"state":"RUNNING",\n"serviceName":"etcd",\n"planName":"free"\n}\n'

    def _run_command_empty_response(self, cmd: list):
        return ''

    def _run_command_return_cmd(self, cmd: list, *, cwd=None, filter_logs=True):
        return cmd

    def _run_command_auth_ok(self, cmd: list):
        return "Authentication succeeded"

    @classmethod
    def setUpClass(cls):
        cls.tap_cli = TapCli("")

    def setUp(self):
        TestTapCli.assertion_errors = 0

    @patch.object(TapCli, "_run_command", _run_command_get_service)
    def test_get_service(self):
        service = self.tap_cli.get_service("test1")
        assert service["name"] == "test1"
        assert service["state"] == "RUNNING"
        assert service["serviceName"] == "etcd"

    @patch.object(TapCli, "_run_command", _run_command_empty_response)
    def test_get_service_empty_response(self):
        with self.assertRaises(AssertionError):
             self.tap_cli.get_service("test1")

    @patch.object(TapCli, "_run_command", _run_command_get_service_command)
    def test_get_service_command(self):
        service = self.tap_cli.get_service("test1")
        assert service["name"] == "test1"

    @patch.object(TapCli, "_run_command", _run_command_get_service_short_command)
    def test_get_service_short_command(self):
        service = self.tap_cli.get_service("test1", short=True)
        assert service["name"] == "test1"

    @patch.object(TapCli, "_run_command", _run_command_get_wrong_service_name)
    def test_get_service_wrong_name(self):
        self.assertRaises(AssertionError, self.tap_cli.get_service, "test1")

    @patch.object(TapCli, "_run_command", _run_command_auth_ok)
    def test_login(self):
        tap_auth = "username", "password"
        assert "Authentication succeeded" == self.tap_cli.login(tap_auth=tap_auth)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_target(self):
        assert ["target"] == self.tap_cli.target()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_help(self):
        assert ["help"] == self.tap_cli.help()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_help_short_command(self):
        assert ["h"] == self.tap_cli.help(short=True)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_version(self):
        assert ["--version"] == self.tap_cli.version()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_version_short_command(self):
        assert ["-v"] == self.tap_cli.version(short=True)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_create_offering(self):
        assert ["create-offering"] == self.tap_cli.create_offering([])

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_create_offering(self):
        assert ["co"] == self.tap_cli.create_offering([], short=True)

    @patch.object(TapCli, "_run_command", _run_command_empty_response)
    def test_create_offering_without_params(self):
        self.assertRaises(TypeError, self.tap_cli.create_offering)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_catalog(self):
        assert ['catalog'] == self.tap_cli.catalog()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_create_service(self):
        assert ["create-service"] == self.tap_cli.create_service([])

    @patch.object(TapCli, "_run_command", _run_command_empty_response)
    def test_create_service_without_params(self):
        self.assertRaises(TypeError, self.tap_cli.create_service)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_delete_service(self):
        assert ["delete-service"] == self.tap_cli.delete_service([])

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_delete_service_short_command(self):
        assert ["ds"] == self.tap_cli.delete_service([], short=True)

    @patch.object(TapCli, "_run_command", _run_command_empty_response)
    def test_delete_service_without_params(self):
        self.assertRaises(TypeError, self.tap_cli.delete_service)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_services_list(self):
        assert ["services"] == self.tap_cli.services_list()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_services_list_short_command(self):
        assert ["svcs"] == self.tap_cli.services_list(short=True)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_service_log(self):
        assert ["logs", "test1"] == self.tap_cli.service_log("test1")

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_service_log_short_command(self):
        assert ["log", "test1"] == self.tap_cli.service_log("test1", short=True)

    test_user = "test_user"

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_invite(self):
        assert ["invite", self.test_user] == self.tap_cli.invite(self.test_user)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_reinvite(self):
        assert ["reinvite", self.test_user] == self.tap_cli.reinvite(self.test_user)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_users(self):
        assert ["users"] == self.tap_cli.users()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_invitations(self):
        assert ["invitations"] == self.tap_cli.invitations()

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_invitations_short_command(self):
        assert ["invs"] == self.tap_cli.invitations(short=True)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_delete_invitations(self):
        assert ["delete-invitation", self.test_user] == self.tap_cli.delete_invitation(self.test_user)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_delete_invitations_short_command(self):
        assert ["di", self.test_user] == self.tap_cli.delete_invitation(self.test_user, short=True)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_delete_user(self):
        assert ["delete-user", self.test_user] == self.tap_cli.delete_user(self.test_user)

    @patch.object(TapCli, "_run_command", _run_command_return_cmd)
    def test_delete_user_short_command(self):
        assert ["du", self.test_user] == self.tap_cli.delete_user(self.test_user, short=True)

    def test_parse_ascii_table(self):
        ascii_table = """
            +-----------------+-------------+-------------------+
            |      NAME       | IMAGE STATE |       STATE       |
            +-----------------+-------------+-------------------+
            | data-repo-app   | READY       | RUNNING           |
            | sample-java-app | PENDING     | WAITING_FOR_IMAGE |
            +-----------------+-------------+-------------------+
        """
        expected_table_data = [
            {
                "NAME":        "data-repo-app",
                "IMAGE STATE": "READY",
                "STATE":       "RUNNING",
            },
            {
                "NAME":        "sample-java-app",
                "IMAGE STATE": "PENDING",
                "STATE":       "WAITING_FOR_IMAGE",
            },
        ]
        assert self.tap_cli.parse_ascii_table(ascii_table) == expected_table_data

    def test_parse_ascii_table_special_chars(self):
        ascii_table = """
            +------+-------+------+
            | PLUS | MINUS | PIPE |
            +------+-------+------+
            |  +   |   -   |  |   |
            +------+-------+------+
        """
        expected_table_data = [
            {
                "PLUS": "+",
                "MINUS": "-",
                "PIPE": "|",
            },
        ]
        assert self.tap_cli.parse_ascii_table(ascii_table) == expected_table_data


if __name__ == "__main__":
    unittest.main()
