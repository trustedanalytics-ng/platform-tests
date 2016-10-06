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

from retry import retry

from modules import test_names
from modules.constants import TapEntityState


class CliService(object):
    MESSAGE_SUCCESS = "CODE: 200 BODY: {\"message\":\"success\"}\nOK"

    FIELD_ID = "id"
    FIELD_NAME = "name"
    FIELD_TYPE = "type"
    FIELD_STATE = "state"
    FIELD_OFFERING_NAME = "serviceName"
    FIELD_PLAN_NAME = "planName"

    def __init__(self, offering_name, plan, name, tap_cli, service_id=None, state=None):
        self.id = service_id
        self.state = state
        self.offering_name = offering_name
        self.plan = plan
        self.name = name
        self.tap_cli = tap_cli

    @classmethod
    def get(cls, name, tap_cli):
        service = tap_cli.get_service(name)
        assert service is not None, "service {} does not exist".format(name)
        return cls(offering_name=service[cls.FIELD_OFFERING_NAME],
                   plan=service[cls.FIELD_PLAN_NAME],
                   name=service[cls.FIELD_NAME],
                   service_id=service[cls.FIELD_ID],
                   state=service[cls.FIELD_STATE],
                   tap_cli=tap_cli)

    @classmethod
    def create(cls, context, tap_cli, offering_name, plan, name=None):
        if name is None:
            name = test_names.generate_test_object_name(separator="-")
        tap_cli.create_service([offering_name, plan.name, name])
        cli_service = cls.get(name, tap_cli)
        context.cli_services.append(cli_service)
        cli_service.ensure_service_state(TapEntityState.RUNNING)
        return cli_service

    def bind(self, bound_service):
        bound_service = bound_service.name if isinstance(bound_service, CliService) else bound_service
        output = self.tap_cli.bind_service([self.name, bound_service])
        assert self.MESSAGE_SUCCESS in output
        return output

    def unbind(self, bound_service):
        bound_service = bound_service.name if isinstance(bound_service, CliService) else bound_service
        output = self.tap_cli.unbind_service([self.name, bound_service])
        assert self.MESSAGE_SUCCESS in output
        return output

    def get_bindings(self):
        return self.tap_cli.bindings(self.name)

    def delete(self):
        return self.tap_cli.delete_service([self.name])

    def cleanup(self):
        self.delete()

    @retry(AssertionError, tries=12, delay=5)
    def ensure_service_state(self, state):
        self.state = self.get(self.name, self.tap_cli).state
        assert self.state == state, "state '{}', expected '{}'".format(self.state, state)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_on_service_list(self):
        assert self.name in self.tap_cli.services_list(), "Instance '{}' is not on the list".format(self.name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_not_on_service_list(self):
        assert self.name not in self.tap_cli.services_list(), "Instance '{}' is on the list".format(self.name)
