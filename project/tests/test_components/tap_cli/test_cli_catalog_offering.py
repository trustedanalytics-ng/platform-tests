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

from modules.constants import TapMessage, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CliOffering
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception


pytestmark = [pytest.mark.components(TAP.cli)]


class TestCliCatalogOffering:
    short = False

    @classmethod
    @pytest.fixture(scope="class")
    def offering(cls, class_context, tap_cli):
        return CliOffering.create(context=class_context, tap_cli=tap_cli)

    @priority.high
    def test_create_and_delete_offering(self, context, tap_cli):
        """
        <b>Description:</b>
        Create offering, check it's show in catalog and remove it.

        <b>Input data:</b>
        -

        <b>Expected results:</b>
        Test passes when offering is created, displayed in catalog and then successfully deleted.

        <b>Steps:</b>
        1. Create offering.
        2. Verify that offering is shown in catalog.
        3. Delete offering.
        4. Verify that offering is not shown in catalog.
        """
        step("Create offering and check it's in catalog")
        offering = CliOffering.create(context=context, tap_cli=tap_cli)
        offering.ensure_in_catalog()
        step("Delete offering and check it's no longer in catalog")
        offering.delete()
        offering.ensure_not_in_catalog()

    @priority.low
    def test_cannot_create_offering_without_parameters(self, tap_cli):
        """
        <b>Description:</b>
        Check that can't create offering without parameters.

        <b>Input data:</b>
        1. Command name: create-offering

        <b>Expected results:</b>
        Attempt to create offering without parameters will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-offering.
        2. Verify that attempt to create offering without parameters will return expected message.
        """
        assert_raises_command_execution_exception(1, TapMessage.NOT_ENOUGH_ARGS_CREATE_OFFERING,
                                                  tap_cli.create_offering, [], self.short)

    @priority.low
    def test_cannot_create_offering_without_json(self, tap_cli):
        """
        <b>Description:</b>
        Check that can't create offering without json.

        <b>Input data:</b>
        1. Command name: create-offering

        <b>Expected results:</b>
        Attempt to create offering without json will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-offering.
        2. Verify that attempt to create offering without json will return expected message.
        """
        invalid_json = generate_test_object_name(separator="-")
        assert_raises_command_execution_exception(1, TapMessage.NO_SUCH_FILE_OR_DIRECTORY.format(invalid_json),
                                                  tap_cli.create_offering, [invalid_json], self.short)

    @priority.low
    def test_create_offering_with_already_used_name(self, context, offering, tap_cli):
        """
        <b>Description:</b>
        Check that can't create offering with already used name.

        <b>Input data:</b>
        1. Command name: create-offering
        2. Existing offering

        <b>Expected results:</b>
        Attempt to create offering with already used name will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-offering.
        2. Verify that attempt to create offering with already used name will return expected message.
        """
        assert_raises_command_execution_exception(1, TapMessage.SERVICE_ALREADY_EXISTS.format(offering.name),
                                                  CliOffering.create, context=context, tap_cli=tap_cli,
                                                  name=offering.name, plans=offering.plans)


class TestCliCatalogOfferingShortCommand(TestCliCatalogOffering):
    short = True
