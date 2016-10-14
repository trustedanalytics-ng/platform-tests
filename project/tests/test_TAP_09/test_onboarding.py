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
from modules.http_calls.platform import user_management
from modules.tap_logger import step
from modules.markers import priority
from modules.tap_object_model import Invitation, User
from modules.tap_object_model.flows import onboarding
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.user_management, TAP.auth_gateway)
pytestmark = [pytest.mark.components(TAP.user_management, TAP.auth_gateway)]


class TestOnboarding:

    @priority.medium
    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    def test_user_cannot_register_already_existing_organization(self, context, test_org):
        step("Invite a new user")
        invitation = Invitation.api_send(context)
        step("Check that an error is returned when the user registers with an already-existing org name")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT,
                                     HttpStatus.MSG_ORGANIZATION_ALREADY_EXISTS.format(test_org.name),
                                     onboarding.register, context=context, code=invitation.code,
                                     username=invitation.username, org_name=test_org.name)
        step("Check that the user was not created")
        username_list = [user.username for user in User.get_all_users()]
        assert invitation.username not in username_list, "User was created"

    @priority.low
    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    def test_user_cannot_register_with_no_organization_name(self, context):
        step("Invite a new user")
        invitation = Invitation.api_send(context)
        step("Check that an error is returned when user registers without passing an org name")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST,
                                     HttpStatus.MSG_ORGANIZATION_CANNOT_CONTAIN_ONLY_WHITESPACES,
                                     user_management.api_register_new_user, code=invitation.code,
                                     password=User.generate_password())
        step("Check that the user was not created")
        username_list = [user.username for user in User.get_all_users()]
        assert invitation.username not in username_list, "User was created"
