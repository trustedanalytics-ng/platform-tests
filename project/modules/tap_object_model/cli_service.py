#
# Copyright (c) 2017 Intel Corporation
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

from retry import retry

from modules.exceptions import ServiceInstanceCreationFailed
from modules import test_names
from modules.constants import TapEntityState
from ._cli_object_superclass import CliObjectSuperclass
from modules.tap_cli import TapCli


class CliService(CliObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["name", "offering_name", "plan_name"]

    MESSAGE_SUCCESS = "OK"

    FIELD_ID = "id"
    FIELD_NAME = "name"
    FIELD_TYPE = "type"
    FIELD_STATE = "state"
    FIELD_OFFERING_NAME = "serviceName"
    FIELD_PLAN_NAME = "planName"

    def __init__(self, offering_name, plan_name, name, tap_cli, service_id=None, state=None):
        super().__init__(tap_cli=tap_cli, name=name)
        self.id = service_id
        self.state = state
        self.offering_name = offering_name
        self.plan_name = plan_name
        self.type = TapCli.SERVICE

    @classmethod
    def get(cls, name, tap_cli):
        service = tap_cli.get_service(name)
        assert service is not None, "service {} does not exist".format(name)
        return cls(offering_name=service[cls.FIELD_OFFERING_NAME],
                   plan_name=service[cls.FIELD_PLAN_NAME],
                   name=service[cls.FIELD_NAME],
                   service_id=service[cls.FIELD_ID],
                   state=service[cls.FIELD_STATE],
                   tap_cli=tap_cli)

    @classmethod
    def create(cls, context, tap_cli, offering_name, plan_name, name=None, envs=None):
        """Creates service instance on platform

        Args:
            context: object context which defined moment of cleanup (e.g. class_context)
            tap_cli: instance Cli client of TAP
            offering_name: name of offering (e.g. mongodb-30)
            plan_name: offering's plan name (e.g. single-small)
            name: name of service instance
            envs: list of environment variables to set inside container
            of created service instance.

        Returns:
            Instance of service instance object.
        """
        name = name if name is not None else \
            test_names.generate_test_object_name(separator="-", short=True)
        cmd = CliService.create_args_list(name, offering_name, plan_name, envs)
        tap_cli.create_service(cmd)
        context.test_objects.append(cls(offering_name=offering_name, plan_name=plan_name,
                                        name=name, tap_cli=tap_cli))
        cli_service = cls.get(name, tap_cli)
        cli_service.ensure_service_state(TapEntityState.RUNNING)
        return cli_service

    def logs(self):
        return self.tap_cli.service_log(self.name)

    def delete(self):
        if self.get(self.name, self.tap_cli).state != TapEntityState.STOPPED:
            self.stop()
            self.ensure_service_state(TapEntityState.STOPPED)
        return self.tap_cli.delete_service(["--name", self.name])

    def cleanup(self):
        self.delete()

    def start(self):
        return self.tap_cli.service_start(self.name)

    def stop(self):
        self.tap_cli.service_stop(self.name)

    def restart(self):
        self.tap_cli.service_restart(self.name)

    def get_details(self):
        return self.tap_cli.get_service(self.name)

    @retry(AssertionError, tries=60, delay=5)
    def ensure_service_state(self, state):
        self.state = self.get(self.name, self.tap_cli).state
        if state != TapEntityState.FAILURE and self.state == TapEntityState.FAILURE:
            raise ServiceInstanceCreationFailed("Instance {} is in state {}".format(self.name, TapEntityState.FAILURE))
        assert self.state == state, "expected state '{}' but was '{}'".format(state, self.state)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_on_service_list(self):
        assert self.name in self.tap_cli.service_list(), "Service '{}' is not on the list of services".format(self.name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_not_on_service_list(self):
        assert self.name not in self.tap_cli.service_list(), "Service '{}' is on the list of services".format(self.name)

    @staticmethod
    def create_args_list(name: str, offering_name: str, plan_name: str, envs: list) -> list:
        """Adds arguments to cli command. Method creates list of arguments to build
        terminal command.

        Args:
            name: name of service to create
            offering_name: name of offering (e.g. mongodb-30)
            plan_name: name od offering's plan (e.g. single-small)
            envs: list of environment variables to set inside container
            of created service instance.

        Returns:
            args: command arguments split into list
        """
        args = ["--offering", offering_name, "--plan", plan_name, "--name", name]
        if envs is None:
            return args
        for env in envs:
            args += ["--env", env]
        return args

    def cleanup(self):
        if self.get_details()[self.FIELD_STATE] == TapEntityState.RUNNING:
            self.stop()
            self.ensure_service_state(TapEntityState.STOPPED)
        self.delete()
