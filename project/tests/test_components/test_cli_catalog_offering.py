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

import pytest
import json

from modules.file_utils import TMP_FILE_DIR, _add_generated_file

from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception
from fixtures.k8s_templates import template_example, catalog_service_example


class TestCliCatalogOffering:
    OFFERING_NAME = generate_test_object_name(separator="-")
    PLAN_NAME = generate_test_object_name(separator="-")
    short = False

    @pytest.fixture(scope="class")
    def example_offer(self):
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
        return example_offer_path

    def test_catalog(self, tap_cli):
        output = tap_cli.catalog()
        assert "CODE: 200" in output

    def test_create_offering(self, example_offer, tap_cli):
        output = tap_cli.create_offering([example_offer], self.short)
        assert 'CODE: 201 BODY:' in output

    def test_check_offering_in_catalog(self, tap_cli, cli_login):
        output = tap_cli.catalog()
        assert self.OFFERING_NAME in output

    def test_create_offering_without_parameters(self, tap_cli):
        error_message = "not enough args: create-offering <path to json with service definition>"
        assert_raises_command_execution_exception(1, error_message, tap_cli.create_offering, [], self.short)

    def test_create_offering_with_not_existing_json(self, tap_cli):
        error_message = "open {}: no such file or directory"
        invalid_json = generate_test_object_name(separator="-")
        output = tap_cli.create_offering([invalid_json], self.short)
        assert error_message.format(invalid_json) in output

    def test_create_offering_with_already_used_name(self, example_offer, tap_cli):
        error_message = "service with name: {} already exists!".format(self.OFFERING_NAME)
        output = tap_cli.create_offering([example_offer], self.short)
        assert error_message in output


class TestCliCatalogOfferingShortCommand(TestCliCatalogOffering):
    OFFERING_NAME = generate_test_object_name(separator="-")
    PLAN_NAME = generate_test_object_name(separator="-")
    short = True
