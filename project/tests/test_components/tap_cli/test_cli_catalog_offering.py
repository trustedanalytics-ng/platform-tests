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

@pytest.mark.usefixtures("cli_login")
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
        Create offering, check it's shown on offering list and remove it.

        <b>Input data:</b>
        -

        <b>Expected results:</b>
        Test passes when offering is created, displayed on offering list and then successfully deleted.

        <b>Steps:</b>
        1. Create offering.
        2. Verify that offering is shown on offering list.
        3. Delete offering.
        4. Verify that offering is not shown on offering list.
        """
        step("Create offering and check it's on offering list")
        offering = CliOffering.create(context=context, tap_cli=tap_cli)
        offering.ensure_on_offering_list()
        step("Delete offering and check it's no longer on offering list")
        offering.delete()
        offering.ensure_not_on_offering_list()

    @priority.medium
    def test_get_offering(self, context, tap_cli):
        """
        <b>Description:</b>
        Create offering, check it can be printed individually and remove it.

        <b>Input data:</b>
        1. Command name: offering info

        <b>Expected results:</b>
        Test passes when offering is created, displayed separately and then successfully deleted.
        After deletion it shall be not printable again.

        <b>Steps:</b>
        1. Create offering.
        2. Verify that offering can be displyed separately.
        3. Cleanup
        """
        step("Create offering and check it's on offering list")
        offering = CliOffering.create(context=context, tap_cli=tap_cli)
        offering.ensure_offering_info_succeed()
        step("Delete offering and check it's no longer on offering list")
        offering.delete()

    @priority.low
    def test_cannot_get_offering_when_doesnt_exist(self, context, tap_cli):
        """
        <b>Description:</b>
        Check that offering details can't be printed when it doesn't exist.

        <b>Input data:</b>
        1. Command name: offering info

        <b>Expected results:</b>
        Test passes when offering is not printable.

        <b>Steps:</b>
        Verify that unexisting offering cannot be displyed (proper message shown)
        """
        assert_raises_command_execution_exception(1, TapMessage.NO_SUCH_OFFERING,
                                                  tap_cli.print_offering, "unexisting")

    @priority.low
    def test_cli_attempt_to_create_offering_with_default_params(self, tap_cli):
        """
        <b>Description:</b>
        Check that CLI tries to create offering from manifest.json if path not provided

        <b>Input data:</b>
        1. Command name: offering create

        <b>Expected results:</b>
        Attempt to create offering without parameters will take manifest.json into account.

        <b>Steps:</b>
        1. Run TAP CLI with command offering create.
        2. Verify that attempt to create offering without parameters will try to use manifest.json file.
        """
        assert_raises_command_execution_exception(1, TapMessage.MANIFEST_JSON_NO_SUCH_FILE,
                                                  tap_cli.create_offering, "")

    @priority.low
    def test_cannot_delete_offering_with_existing_instance(self, tap_cli, mysql_instance):
        """
        <b>Description:</b>
        Check that CLI cannot delete offering that has instance created

        <b>Input data:</b>
        1. Command name: offering delete

        <b>Expected results:</b>
        Attempt to delete offering with existing instance is forbidden. Explanation displayed.

        <b>Steps:</b>
        1. Make sure mysql instance is on platform.
        2. Try to delete mysql offering.
        3. Verify that attempt to delete offering will end up with proper message shown.
        """
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_DELETE_OFFERING_WITH_INSTANCE,
                                                  tap_cli.delete_offering, mysql_instance.offering_label)

    @priority.low
    def test_cannot_create_offering_without_json(self, tap_cli):
        """
        <b>Description:</b>
        Check that can't create offering without providing json for manifest flag.

        <b>Input data:</b>
        1. Command name: offering create

        <b>Expected results:</b>
        Attempt to create offering without json will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command offering create.
        2. Verify that attempt to create offering without json will return expected message.
        """
        invalid_json = generate_test_object_name(separator="-")
        assert_raises_command_execution_exception(1, TapMessage.NO_SUCH_FILE_OR_DIRECTORY.format(invalid_json),
                                                  tap_cli.create_offering, invalid_json)

    @priority.low
    def test_cannot_create_offering_with_already_used_name(self, context, offering, tap_cli):
        """
        <b>Description:</b>
        Check that can't create offering with already used name.

        <b>Input data:</b>
        1. Command name: offering create
        2. Existing offering

        <b>Expected results:</b>
        Attempt to create offering with already used name will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command offering create.
        2. Verify that attempt to create offering with already used name will return expected message.
        """
        assert_raises_command_execution_exception(1, TapMessage.SERVICE_ALREADY_EXISTS.format(offering.name),
                                                  CliOffering.create, context=context, tap_cli=tap_cli,
                                                  name=offering.name, plans=offering.plans)

