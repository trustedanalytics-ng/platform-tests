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

import os
import json

from retry import retry

import config
from modules.constants import RelativeRepositoryPaths
from modules import command


class TapCli:
    TARGET = "target"
    HELP = "help", "h"
    VERSION = "--version", "-v"
    LOGIN = "login"
    CREATE_OFFERING = "create-offering", "co"
    CATALOG = "catalog"
    CREATE_SERVICE = "create-service", "cs"
    DELETE_SERVICE = "delete-service", "ds"
    SERVICES = "services", "svcs"
    SERVICE = "service", "s"
    LOGS = "logs", "log"

    def __init__(self, cli_app_path):
        self.command = os.path.join(cli_app_path, RelativeRepositoryPaths.tap_cli)

    def _run_command(self, cmd: list):
        cmd = [self.command] + cmd
        output = command.run(cmd)
        return "\n".join(output)

    def login(self, login_domain=config.cf_api_url, tap_auth=None):
        if tap_auth is None:
            tap_auth = config.ng_k8s_service_credentials()
        return self._run_command([self.LOGIN, login_domain, tap_auth[0], tap_auth[1]])

    def target(self):
        return self._run_command([self.TARGET])

    def help(self, short=False):
        return self._run_command([self.HELP[1] if short else self.HELP[0]])

    def version(self, short=False):
        return self._run_command([self.VERSION[1] if short else self.VERSION[0]])

    def create_offering(self, cmd: list, short=False):
        return self._run_command([self.CREATE_OFFERING[1] if short else self.CREATE_OFFERING[0]] + cmd)

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

    def get_service(self, service_name, short=False):
        output = self._run_command([self.SERVICE[1] if short else self.SERVICE[0], service_name])
        try:
            service_json = output.split(sep="BODY:")[2].split(sep="\n")[0]
        except IndexError:
            return None
        service = json.loads(service_json)
        assert service['name'] == service_name
        return service

    @retry(AssertionError, tries=30, delay=2)
    def ensure_service_state(self, service_name, state):
        service = self.get_service(service_name)
        assert service is not None, "service {} does not exist".format(service_name)
        assert service["state"] == state, "expected state '{}' but was '{}'".format(state, service['state'])

