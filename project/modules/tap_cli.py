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
    INFO = "info"
    HELP = "help", "h"
    VERSION = "--version", "-v"
    LOGIN = "login"
    CREATE_OFFERING = ["offering", "create"]
    DELETE_OFFERING = ["offering", "delete"]
    LIST_OFFERINGS = ["offering", "list"]
    GET_OFFERING = ["offering", "info"]
    HELP_OFFERING = ["offering", "help"]
    CREATE_SERVICE = ["service", "create"]
    DELETE_SERVICE = ["service", "delete"]
    SERVICE = "service"
    SERVICES = ["service", "list"]
    SERVICE_INFO = ["service", "info"]
    SERVICE_LOGS = ["service", "logs", "show"]
    SERVICE_START = ["service", "start"]
    SERVICE_STOP = ["service", "stop"]
    SERVICE_CREDENTIALS = ["service", "credentials", "show"]
    APPLICATION = "application"
    APPLICATION_INFO = ["application", "info"]
    APPLICATION_LIST = ["application", "list"]
    APPLICATION_PUSH = ["application", "push"]
    APPLICATION_DELETE = ["application", "delete"]
    APPLICATION_START = ["application", "start"]
    APPLICATION_STOP = ["application", "stop"]
    APPLICATION_RESTART = ["application", "restart"]
    APPLICATION_SCALE = ["application", "scale"]
    APPLICATION_LOGS_SHOW = ["application", "logs", "show"]
    BINDING = "binding"
    BINDING_CREATE =  ["binding","create"]
    BINDING_DELETE =  ["binding","delete"]
    BINDING_LIST = ["binding","list"]
    INVITE = ["user", "invitation", "send"]
    HELP_INVITATION = ["user", "invitation", "help"]
    REINVITE = ["user", "invitation", "resend"]
    USERS = ["user", "list"]
    HELP_USER = ["user", "help"]
    INVITATIONS = ["user", "invitation", "list"]
    DELETE_INVITATION = ["user", "invitation", "delete"]
    DELETE_USER = ["user", "delete"]
    PASSWORD_CHANGE = ["user", "passwd"]

    HELP_FLAG = "--help"
    API_PARAM = "--api"
    USERNAME_PARAM = "--username"
    PASSWORD_PARAM = "--password"
    EMAIL_PARAM = "--email"
    NAME_PARAM = "--name"
    MANIFEST_PARAM = "--manifest"
    CURRENT_PASSWD = "--current"
    NEW_PASSWD = "--new"
    YES_PARAM = "--yes"
    REPLICAS_PARAM = "--replicas"
    ARCHIVE_PATCH_PARAM = "--archive-path"
    SRC_NAME_PARAM = "--src-name"
    DST_NAME_PARAM = "--dst-name"
    IS_DST_PARAM = "--is-dst"

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
        output = self._run_command([self.LOGIN,
                                    self.API_PARAM, "http://{}".format(login_domain),
                                    self.USERNAME_PARAM, tap_auth[0],
                                    self.PASSWORD_PARAM, tap_auth[1]])
        if TapMessage.AUTHENTICATION_SUCCEEDED not in output:
            raise TapCliException(output)
        return output

    def info(self):
        return self._run_command([self.INFO])

    def help(self, short=False):
        return self._run_command([self.HELP[1] if short else self.HELP[0]])

    def offering_help(self):
        return self._run_command(self.HELP_OFFERING)

    def user_help(self):
        return self._run_command(self.HELP_USER)

    def invitation_help(self):
        return self._run_command(self.HELP_INVITATION)

    def service_binding_help(self):
        return self._run_command([self.SERVICE, self.BINDING, self.HELP[0]])

    def application_binding_help(self):
        return self._run_command([self.APPLICATION, self.BINDING, self.HELP[0]])

    def version(self, short=False):
        return self._run_command([self.VERSION[1] if short else self.VERSION[0]])

    def create_offering(self, manifest_path: str):
        return self._run_command(self.CREATE_OFFERING +
                                 ([self.MANIFEST_PARAM, manifest_path] if manifest_path else []))

    def delete_offering(self, offering_name: str):
        return self._run_command(self.DELETE_OFFERING + [self.NAME_PARAM, offering_name, self.YES_PARAM])

    def list_offerings(self):
        return self._run_command(self.LIST_OFFERINGS)

    def print_offering(self, offering_name: str):
        return self._run_command(self.GET_OFFERING + [self.NAME_PARAM, offering_name])

    def create_service(self, cmd: list):
        return self._run_command(self.CREATE_SERVICE + cmd)

    def delete_service(self, cmd: list):
        return self._run_command(self.DELETE_SERVICE + cmd + [self.YES_PARAM])

    def services_list(self):
        return self._run_command(self.SERVICES)

    def service_log(self, service_name):
        return self._run_command(self.SERVICE_LOGS + [self.NAME_PARAM, service_name],
                                 filter_logs=False)

    def service_credentials(self, cmd):
        return self._run_command(self.SERVICE_CREDENTIALS + cmd)

    def service_stop(self, service_name):
        return self._run_command(self.SERVICE_STOP + [self.NAME_PARAM, service_name], filter_logs=False)

    def bindings(self, instance_type, instance_name, direction):
        output = self._run_command([instance_type] + self.BINDING_LIST + [self.NAME_PARAM, instance_name, direction])
        bindings = self.parse_ascii_table(output)
        return bindings

    def bind(self, instance_type,  cmd: list):
        return self._run_command([instance_type] + self.BINDING_CREATE + cmd)

    def unbind(self, instance_type, cmd: list):
        return self._run_command([instance_type] + self.BINDING_DELETE + cmd)

    def get_service(self, service_name):
        output = self._run_command(self.SERVICE_INFO + [self.NAME_PARAM, service_name])
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

    def app_list(self):
        ascii_table = self._run_command(self.APPLICATION_LIST)
        return self.parse_ascii_table(ascii_table)

    def app_info(self, application_name):
        output = self._run_command(self.APPLICATION_INFO + [self.NAME_PARAM, application_name])
        app_json = output[output.find("{"):output.rfind("}")+1]
        app = json.loads(app_json)
        assert isinstance(app, dict)
        assert app['name'] == application_name
        return app

    def app_push(self, *, app_path):
        """Push an application.
        If the path is a file, it is assumed it is an archived application, otherwise,
        that the path is a directory containing the application files.

        Args:
            app_dir_path: Path to an archived application or to the application directory

        Returns:
            Command output
        """
        if os.path.isfile(app_path):
            cmd = self.APPLICATION_PUSH + [self.ARCHIVE_PATCH_PARAM, os.path.basename(app_path)]
            cwd = os.path.dirname(app_path)
        else:
            cmd = self.APPLICATION_PUSH
            cwd = app_path
        return self._run_command(cmd, cwd=cwd)

    def app_delete(self, application_name):
        return self._run_command(self.APPLICATION_DELETE + [self.NAME_PARAM, application_name, self.YES_PARAM])

    def app_start(self, application_name):
        return self._run_command(self.APPLICATION_START + [self.NAME_PARAM, application_name])

    def app_stop(self, application_name):
        return self._run_command(self.APPLICATION_STOP + [self.NAME_PARAM, application_name])

    def app_restart(self, application_name: str):
        """Restarts the application

        Args:
            application_name: Name of the application to restart

        Returns:
            Output of the command

        Raises:
            CommandExecutionException
        """
        return self._run_command(self.APPLICATION_RESTART + [self.NAME_PARAM, application_name])

    def app_scale(self, application_name, instances):
        return self._run_command(self.APPLICATION_SCALE + [self.NAME_PARAM, application_name, self.REPLICAS_PARAM, instances])

    def app_logs(self, application_name):
        return self._run_command(self.APPLICATION_LOGS_SHOW + [self.NAME_PARAM, application_name])

    def app_push_help(self):
        return self._run_command(self.APPLICATION_PUSH + [self.HELP_FLAG])

    def invite(self, username):
        return self._run_command(self.INVITE + [self.EMAIL_PARAM, username])

    def reinvite(self, username):
        return self._run_command(self.REINVITE + [self.EMAIL_PARAM, username])

    def users(self):
        return self._run_command(self.USERS)

    def invitations(self):
        return self._run_command(self.INVITATIONS)

    def delete_invitation(self, username):
        return self._run_command(self.DELETE_INVITATION + [self.EMAIL_PARAM, username, self.YES_PARAM])

    def delete_user(self, username):
        return self._run_command(self.DELETE_USER + [self.NAME_PARAM, username, self.YES_PARAM])

    def change_password(self, current, new):
        params = [self.CURRENT_PASSWD, current, self.NEW_PASSWD, new]
        return self._run_command(self.PASSWORD_CHANGE + params)

    @staticmethod
    def parse_ascii_table(ascii_table):
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
