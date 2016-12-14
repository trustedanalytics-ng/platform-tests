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

import json
import os
import re

import config
from modules import command
from modules.constants import TapMessage
from modules.exceptions import TapCliException


class TapCli:
    TARGET = "target"
    HELP = "help", "h"
    VERSION = "--version", "-v"
    LOGIN = "login"
    CREATE_OFFERING = "create-offering", "co"
    DELETE_OFFERING = "delete-offering", "do"
    CATALOG = "catalog"
    CREATE_SERVICE = "create-service", "cs"
    DELETE_SERVICE = "delete-service", "ds"
    SERVICES = "services", "svcs"
    SERVICE = "service", "s"
    SERVICE_STOP = "service-stop"
    LOGS = "logs", "log"
    PUSH = "push"
    APP = "application"
    APPS = "applications"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    SCALE = "scale"
    DELETE = "delete"
    PUSH_HELP = [PUSH, "--help"]
    BINDINGS = "bindings"
    BIND = "bind-instance", "bind"
    UNBIND = "unbind-instance", "unbind"
    INVITE = "invite"
    REINVITE = "reinvite"
    USERS = "users"
    INVITATIONS = "invitations", "invs"
    DELETE_INVITATION = "delete-invitation", "di"
    DELETE_USER = "delete-user", "du"

    LOGLINE_PATTERN = '[-,.:0-9 ]{1,20}(CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET)'

    def __init__(self, cli_app_path):
        self.command = cli_app_path

    @staticmethod
    def is_logline(line):
        return bool(re.match(TapCli.LOGLINE_PATTERN, line))

    def _run_command(self, cmd: list, *, cwd=None, filter_logs=True):
        cmd = [self.command] + cmd
        output = command.run(cmd, cwd=cwd)
        if filter_logs:
            output = [line for line in output if not TapCli.is_logline(line)]
        output = "\n".join(output)
        return output

    def login(self, login_domain=config.api_url, tap_auth=None):
        if tap_auth is None:
            tap_auth = [config.admin_username, config.admin_password]
        output = self._run_command([self.LOGIN, "http://{}".format(login_domain), tap_auth[0], tap_auth[1]])
        if TapMessage.AUTHENTICATION_SUCCEEDED not in output:
            raise TapCliException(output)
        return output

    def target(self):
        return self._run_command([self.TARGET])

    def help(self, short=False):
        return self._run_command([self.HELP[1] if short else self.HELP[0]])

    def version(self, short=False):
        return self._run_command([self.VERSION[1] if short else self.VERSION[0]])

    def create_offering(self, cmd: list, short=False):
        return self._run_command([self.CREATE_OFFERING[1] if short else self.CREATE_OFFERING[0]] + cmd)

    def delete_offering(self, cmd: list, short=False):
        return self._run_command([self.DELETE_OFFERING[1] if short else self.DELETE_OFFERING[0]] + cmd)

    def catalog(self):
        return self._run_command([self.CATALOG])

    def create_service(self, cmd: list, short=False):
        return self._run_command([self.CREATE_SERVICE[1] if short else self.CREATE_SERVICE[0]] + cmd)

    def delete_service(self, cmd: list, short=False):
        return self._run_command([self.DELETE_SERVICE[1] if short else self.DELETE_SERVICE[0]] + cmd)

    def services_list(self, short=False):
        return self._run_command([self.SERVICES[1] if short else self.SERVICES[0]])

    def service_log(self, service_name, short=False):
        return self._run_command([self.LOGS[1] if short else self.LOGS[0], service_name],
                                 filter_logs=False)

    def service_stop(self, service_name):
        return self._run_command([self.SERVICE_STOP, service_name], filter_logs=False)

    def bindings(self, instance_name):
        output = self._run_command([self.BINDINGS, instance_name])
        bindings = self.parse_ascii_table(output)
        return bindings

    def bind_service(self, cmd: list, short=False):
        return self._run_command([self.BIND[1] if short else self.BIND[0]] + cmd)

    def unbind_service(self, cmd: list, short=False):
        return self._run_command([self.UNBIND[1] if short else self.UNBIND[0]] + cmd)

    def get_service(self, service_name, short=False):
        output = self._run_command([self.SERVICE[1] if short else self.SERVICE[0], service_name])
        # TODO: Fix ".replace('}OK', '}')" (workaround for JSON diversity)
        output_lines = [line.strip().replace('}OK', '}') for line in output.split("\n")]
        try:
            json_start = output_lines.index("{")
            json_stop = [i for i, item in enumerate(output_lines) if item == "}"][-1]
        except (ValueError, IndexError):
            raise AssertionError("Cannot parse command output as json: {}".format(output))
        output_json = json.loads("\n".join(output_lines[json_start:json_stop+1]))
        assert output_json["name"] == service_name
        return output_json

    def push(self, *, app_path):
        """Push an application.
        If the path is a file, it is assumed it is an archived application, otherwise,
        that the path is a directory containing the application files.

        Args:
            app_dir_path: Path to an archived application or to the application directory

        Returns:
            Command output
        """
        if os.path.isfile(app_path):
            cmd = [self.PUSH, os.path.basename(app_path)]
            cwd = os.path.dirname(app_path)
        else:
            cmd = [self.PUSH]
            cwd = app_path
        return self._run_command(cmd, cwd=cwd)

    def apps(self):
        ascii_table = self._run_command([self.APPS])
        return self.parse_ascii_table(ascii_table)

    def app(self, application_name):
        output = self._run_command([self.APP, application_name])
        app_json = output[output.find("{"):output.rfind("}")+1]
        app = json.loads(app_json)
        assert isinstance(app, dict)
        assert app['name'] == application_name
        return app

    def start_app(self, application_name):
        return self._run_command([self.START, application_name])

    def stop_app(self, application_name):
        return self._run_command([self.STOP, application_name])

    def restart_app(self, application_name: str):
        """Restarts the application

        Args:
            application_name: Name of the application to restart

        Returns:
            Output of the command

        Raises:
            CommandExecutionException
        """
        return self._run_command([self.RESTART, application_name])

    def scale_app(self, application_name, instances):
        return self._run_command([self.SCALE, application_name, instances])

    def app_logs(self, application_name):
        return self._run_command([self.LOGS[1], application_name])

    def delete_app(self, application_name):
        return self._run_command([self.DELETE, application_name])

    def push_help(self):
        return self._run_command(self.PUSH_HELP)

    def invite(self, username):
        return self._run_command([self.INVITE, username])

    def reinvite(self, username):
        return self._run_command([self.REINVITE, username])

    def users(self):
        return self._run_command([self.USERS])

    def invitations(self, short=False):
        return self._run_command([self.INVITATIONS[1] if short else self.INVITATIONS[0]])

    def delete_invitation(self, username, short=False):
        return self._run_command([self.DELETE_INVITATION[1] if short else self.DELETE_INVITATION[0], username])

    def delete_user(self, username, short=False):
        return self._run_command([self.DELETE_USER[1] if short else self.DELETE_USER[0], username])

    def parse_ascii_table(self, ascii_table):
        cut_pos = []
        ranges = []

        def assert_frame_line(line):
            for i in range(len(line)):
                assert line[i] == ("+" if i in cut_pos else "-"), "Wrong format of ascii table"

        def parse_data_line(line):
            for i in cut_pos:
                assert line[i] == "|", "Misaligned ascii table"
            data = [line[i+1:j].strip() for (i, j) in ranges]
            return data

        lines = [line.strip() for line in ascii_table.strip().splitlines()]
        cut_pos = [i for i in range(len(lines[0]))
                   if lines[0][i] == "+"]
        ranges = [(cut_pos[i], cut_pos[i+1])
                  for i in range(len(cut_pos)-1)]
        assert_frame_line(lines[0])
        assert_frame_line(lines[2])
        assert_frame_line(lines[-1])
        headers = parse_data_line(lines[1])
        data = [dict(zip(headers,
                         parse_data_line(line)))
                for line in lines[3:-1]]
        return data
