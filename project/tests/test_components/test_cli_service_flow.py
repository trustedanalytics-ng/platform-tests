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

import pytest
from modules.markers import incremental

from fixtures.k8s_templates import template_example
from fixtures.k8s_templates import catalog_service_example
from modules.file_utils import TMP_FILE_DIR, _add_generated_file
from modules.tap_logger import step
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception


class TestCliServiceFlow:
    OFFERING_NAME = None
    PLAN_NAME = None
    SERVICE_INSTANCE_NAME = None

    @pytest.fixture(scope="class")
    def example_offer(self, tap_cli):
        assert self.OFFERING_NAME is not None
        assert self.PLAN_NAME is not None
        example_offer_path = TMP_FILE_DIR + "/" + self.OFFERING_NAME
        data = {}
        template = template_example.etcd_template
        service = catalog_service_example.etcd_example
        service["name"] = self.OFFERING_NAME
        service["plans"][0]['name'] = self.PLAN_NAME
        data['template'] = template
        data['services'] = [service]

        with open(example_offer_path, "w") as text_file:
            print(json.dumps(data), file=text_file)

        _add_generated_file(example_offer_path)
        output = tap_cli.create_offering([example_offer_path])
        assert 'CODE: 201 BODY:' in output


class TestCliServiceCornerCases(TestCliServiceFlow):
    OFFERING_NAME = generate_test_object_name(separator="-")
    PLAN_NAME = generate_test_object_name(separator="-")
    SERVICE_INSTANCE_NAME = generate_test_object_name(separator="-")
    short = False

    def test_create_service_instance_with_invalid_plan(self, tap_cli, example_offer, cli_login):
        step("Check that create service return information about lack of provided plan")
        invalid_service_plan = 'shared'
        output = tap_cli.create_service([self.OFFERING_NAME, invalid_service_plan, 'test1'], self.short)
        assert "cannot find plan: '{}' for service: '{}'".format(invalid_service_plan,
                                                                 self.OFFERING_NAME) in output

    def test_create_service_instance_without_instance_name(self, tap_cli, cli_login):
        step("Check that create service return error with information about lack of arguments")
        error_message = "not enough args: create-service <service_name> <plan_name> <custom_name>"
        assert_raises_command_execution_exception(1, error_message, tap_cli.create_service,
                                                  [self.OFFERING_NAME, self.PLAN_NAME], self.short)

    def test_create_service_instance_without_plan(self, tap_cli, cli_login):
        step("Check that create service return error with information about lack of arguments")
        error_message = "not enough args: create-service <service_name> <plan_name> <custom_name>"
        assert_raises_command_execution_exception(1, error_message, tap_cli.create_service,
                                                  [self.OFFERING_NAME, "test"], self.short)

    def test_create_service_instance_without_offering(self, tap_cli, cli_login):
        step("Check that create service return error with information about lack of arguments")
        error_message = "not enough args: create-service <service_name> <plan_name> <custom_name>"
        assert_raises_command_execution_exception(1, error_message, tap_cli.create_service, [self.PLAN_NAME, "test"],
                                                  self.short)

    def test_create_service_instance_with_invalid_service_name(self, tap_cli, cli_login):
        step("Check that create service return information about lack of provided service name")
        invalid_service_name = "logstashxyz"
        output = tap_cli.create_service([invalid_service_name, 'free', 'test1'], self.short)
        assert "cannot find service: '{}'".format(invalid_service_name) in output

    def test_invalid_instance_name_service_log(self, tap_cli, cli_login):
        step("Check that information about lack of service will shown")
        invalid_service_name = generate_test_object_name(separator="-")
        output = tap_cli.service_log(invalid_service_name, self.short)
        assert "cannot find instance with name: {}".format(invalid_service_name) in output

    def test_delete_service_without_providing_all_required_arguments(self, tap_cli, cli_login):
        step("Check that delete service return error with information about lack of arguments")
        assert_raises_command_execution_exception(1, 'not enough args: delete-service <service_custom_name>',
                                                  tap_cli.delete_service, [], self.short)

    def test_delete_service_with_invalid_name(self, tap_cli, cli_login):
        step("Check that information about lack of service will shown")
        invalid_service_name = generate_test_object_name(separator="-")
        output = tap_cli.delete_service([invalid_service_name], self.short)
        assert "cannot find instance with name: {}".format(invalid_service_name) in output


class TestCliServiceCornerCasesShortCommand(TestCliServiceCornerCases):
    OFFERING_NAME = generate_test_object_name(separator="-")
    PLAN_NAME = generate_test_object_name(separator="-")
    SERVICE_INSTANCE_NAME = generate_test_object_name(separator="-")
    short = False


@incremental
class TestCliService(TestCliServiceFlow):
    OFFERING_NAME = generate_test_object_name(separator="-")
    PLAN_NAME = generate_test_object_name(separator="-")
    SERVICE_INSTANCE_NAME = generate_test_object_name(separator="-")
    short = False

    def test_1_create_service_instance(self, tap_cli, example_offer, cli_login):
        step("Check that user can create service instance")
        output = tap_cli.create_service([self.OFFERING_NAME, self.PLAN_NAME, self.SERVICE_INSTANCE_NAME],
                                        self.short)
        assert 'CODE: 202 BODY: ' in output
        tap_cli.ensure_service_state(self.SERVICE_INSTANCE_NAME, "RUNNING")
        state = tap_cli.get_service(self.SERVICE_INSTANCE_NAME)['state']
        assert state == "RUNNING"

    def test_3_service_list(self, tap_cli, cli_login):
        step("Check that created service is visible on services list")
        output = tap_cli.services_list()
        assert self.OFFERING_NAME in output
        assert self.PLAN_NAME in output
        assert self.SERVICE_INSTANCE_NAME in output

    def test_4_get_service_logs(self, tap_cli, cli_login):
        step("Check that logs are shown")
        output = tap_cli.service_log(self.SERVICE_INSTANCE_NAME, self.short)
        assert "OK" in output.split("\n")[-1]

    def test_5_delete_service(self, tap_cli, cli_login):
        step("Check that service instance will be deleted properly")
        output = tap_cli.delete_service([self.SERVICE_INSTANCE_NAME], self.short)
        assert 'CODE: 202 BODY: ""\nOK' in output


@incremental
class TestCliServiceShortCommand(TestCliService):
    OFFERING_NAME = generate_test_object_name(separator="-")
    PLAN_NAME = generate_test_object_name(separator="-")
    SERVICE_INSTANCE_NAME = generate_test_object_name(separator="-")
    short = True
