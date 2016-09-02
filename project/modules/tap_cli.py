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

import config
from modules.constants import RelativeRepositoryPaths
from modules import command


class TapCli(object):
    TARGET = "target"
    HELP = "help"
    VERSION = "--version"
    LOGIN = "login"

    def __init__(self, cli_app_path):
        self.command = os.path.join(cli_app_path, RelativeRepositoryPaths.tap_cli)

    def _run_command(self, cmd: list):
        cmd = [self.command] + cmd
        output = command.run(cmd, return_output=True)
        return "\n".join(output)

    def login(self, login_domain=config.cf_api_url, tap_auth=None):
        if tap_auth is None:
            tap_auth = config.ng_k8s_service_credentials()
        return self._run_command([self.LOGIN, login_domain, tap_auth[0], tap_auth[1]])

    def target(self):
        return self._run_command([self.TARGET])

    def help(self):
        return self._run_command([self.HELP])

    def version(self):
        return self._run_command([self.VERSION])
