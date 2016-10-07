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

from retry import retry

import config
from modules import command
from modules.constants import HttpStatus, TapMessage
from modules.exceptions import TapCliException
from modules.http_client import HttpClientFactory
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider


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
    LOGS = "logs", "log"
    PUSH = "push"
    APP = "application"
    APPS = "applications"
    START = "start"
    STOP = "stop"
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

    def __init__(self, cli_app_path):
        self.command = cli_app_path

    def _run_command(self, cmd: list, cwd=None):
        cmd = [self.command] + cmd
        output = command.run(cmd, cwd=cwd)
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
        return self._run_command([self.LOGS[1] if short else self.LOGS[0], service_name])

    def bindings(self, instance_name):
        output = self._run_command([self.BINDINGS, instance_name])
        bindings = output.split("CODE: 200 BODY:")[-1].split("\n")[0]
        return bindings

    def bind_service(self, cmd: list, short=False):
        return self._run_command([self.BIND[1] if short else self.BIND[0]] + cmd)

    def unbind_service(self, cmd: list, short=False):
        return self._run_command([self.UNBIND[1] if short else self.UNBIND[0]] + cmd)

    def get_service(self, service_name, short=False):
        output = self._run_command([self.SERVICE[1] if short else self.SERVICE[0], service_name])
        try:
            service_json = output.split(sep="BODY:")[2].split(sep="\n")[0]
        except IndexError:
            return None
        service = json.loads(service_json)
        assert service['name'] == service_name
        return service

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
        return self._run_command([self.APPS])

    def app(self, application_name):
        output = self._run_command([self.APP, application_name])
        try:
            app_json = output.split(sep="BODY:")[2].split(sep="\n")[0]
        except IndexError:
            return None
        app = json.loads(app_json)
        assert isinstance(app, dict)
        assert app['name'] == application_name
        return app

    def start_app(self, application_name):
        return self._run_command([self.START, application_name])

    def stop_app(self, application_name):
        return self._run_command([self.STOP, application_name])

    def scale_app(self, application_name, instances):
        return self._run_command([self.SCALE, application_name, instances])

    def app_logs(self, application_name):
        return self._run_command([self.LOGS[1], application_name])

    def delete_app(self, application_name):
        return self._run_command([self.DELETE, application_name])

    def push_help(self):
        return self._run_command(self.PUSH_HELP)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_availability_on_the_list(self, application_name, should_be_on_the_list: bool):
        apps = self.apps()
        if should_be_on_the_list:
            assert application_name in apps, "App '{}' is not on the list of apps".format(application_name)
        else:
            assert application_name not in apps, "App '{}' is still on the list of apps".format(application_name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_state(self, application_name, state):
        app = self.app(application_name=application_name)
        assert app is not None, "App {} does not exist".format(app)
        assert app["state"] == state, "Expected state '{}' but was '{}'".format(state, app['state'])

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_is_ready(self, application_url):
        client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=application_url))
        response = client.request(
            method=HttpMethod.GET,
            path="",
            raw_response=True,
            raise_exception=True,
            msg="Application: get /{}".format("")
        )
        assert response.status_code == HttpStatus.CODE_OK

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
