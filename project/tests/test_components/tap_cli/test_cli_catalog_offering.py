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

from modules.constants import TapMessage
from modules.tap_logger import step
from modules.tap_object_model import CliOffering
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception


class TestCliCatalogOffering:
    short = False

    @classmethod
    @pytest.fixture(scope="class")
    def offering(cls, class_context, tap_cli):
        return CliOffering.create(context=class_context, tap_cli=tap_cli)

    def test_create_and_delete_offering(self, context, tap_cli):
        step("Create offering and check it's in catalog")
        offering = CliOffering.create(context=context, tap_cli=tap_cli)
        offering.ensure_in_catalog()
        step("Delete offering and check it's no longer in catalog")
        offering.delete()
        offering.ensure_not_in_catalog()

    def test_cannot_create_offering_without_parameters(self, tap_cli):
        assert_raises_command_execution_exception(1, TapMessage.NOT_ENOUGH_ARGS_CREATE_OFFERING,
                                                  tap_cli.create_offering, [], self.short)

    def test_cannot_create_offering_without_json(self, tap_cli):
        invalid_json = generate_test_object_name(separator="-")
        output = tap_cli.create_offering([invalid_json], self.short)
        assert TapMessage.NO_SUCH_FILE_OR_DIRECTORY.format(invalid_json) in output

    def test_create_offering_with_already_used_name(self, context, offering, tap_cli):
        with pytest.raises(AssertionError) as e:
            CliOffering.create(context=context, tap_cli=tap_cli, name=offering.name, plans=offering.plans)
        assert TapMessage.SERVICE_ALREADY_EXISTS.format(offering.name) in e.value.msg


class TestCliCatalogOfferingShortCommand(TestCliCatalogOffering):
    short = True
