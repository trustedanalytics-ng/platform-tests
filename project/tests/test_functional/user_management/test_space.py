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

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, Space, User
from tests.fixtures.assertions import assert_not_in_with_retry, assert_raises_http_exception
from config import tap_type
from config import TapType

logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]
tap_ng = TapType.tap_ng.value

@pytest.mark.skipif(tap_type == tap_ng, reason="Spaces are not predicted for TAP_NG")
class TestSpace:

    @priority.medium
    def test_get_spaces_list_in_new_org(self, context):
        step("Create new organization")
        org = Organization.api_create(context)
        step("Get list of spaces in the org and check that there are none")
        spaces = Space.api_get_list_in_org(org_guid=org.guid)
        assert len(spaces) == 0, "There are spaces in a new organization"

    @priority.high
    def test_create_and_delete_space(self, test_org):
        step("Create new space in the organization")
        space = Space.api_create(org=test_org)
        step("Check that the space is on the org space list")
        spaces = Space.api_get_list()
        assert space in spaces
        step("Delete the test space")
        space.api_delete()
        assert_not_in_with_retry(space, Space.api_get_list)

    @priority.medium
    def test_cannot_create_space_with_existing_name(self, test_org):
        step("Create a space")
        space = Space.api_create(org=test_org)
        step("Check that attempt to create a space with the same name in the same org returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST, Space.api_create,
                                     org=test_org, name=space.name)

    @priority.low
    def test_create_space_with_long_name(self, test_org):
        step("Create space with name 400 char long")
        long_name = Space.NAME_PREFIX + "t" * 400
        space = Space.api_create(org=test_org, name=long_name)
        step("Check that the space with long name is present on space list")
        spaces = Space.api_get_list()
        assert space in spaces

    @priority.low
    def test_create_space_with_empty_name(self, test_org):
        step("Check that attempt to create space with empty name returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST, Space.api_create,
                                     name="", org=test_org)

    @priority.low
    def test_cannot_delete_not_existing_space(self, test_org):
        step("Create a space")
        space = Space.api_create(org=test_org)
        step("Delete the space")
        space.api_delete()
        assert_not_in_with_retry(space, Space.api_get_list)
        step("Check that attempt to delete the space again returns an error")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND, space.api_delete)

    @priority.low
    def test_cannot_delete_space_with_user(self, context, test_org):
        step("Create a space")
        space = Space.api_create(org=test_org)
        step("Add new platform user to the space")
        User.api_create_by_adding_to_space(context, org_guid=test_org.guid, space_guid=space.guid)
        step("Delete the space")
        space.api_delete()
        step("Check that the space is not on the space list")
        assert_not_in_with_retry(space, Space.api_get_list)
