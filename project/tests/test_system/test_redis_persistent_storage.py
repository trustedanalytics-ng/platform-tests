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

from modules.constants import TapComponent as TAP, Guid
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import KubernetesPod
from modules.tap_object_model.flows import onboarding
from modules.tap_object_model.invitation import Invitation
from modules.tap_object_model.user import User
from tests.fixtures.assertions import assert_user_in_org_and_role

logged_components = (TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestRedisPersitentStorage:
    POD_NAME_PREFIX = "user-management"

    @pytest.mark.usefixtures("open_tunnel")
    @priority.low
    def test_use_invitation_after_pod_restart(self, context):
        """
        <b>Description:</b>
        Checks if user invitation is valid after user-management POD restart.

        <b>Input data:</b>
        1. User name.
        2. Password.

        <b>Expected results:</b>
        Test passes when user was correctly added to the platform.

        <b>Steps:</b>
        1. Invite new user.
        2. Restart user-management POD.
        3. Register user with the invitation.
        """

        step("Invite new user")
        invitation = Invitation.api_send(context)

        step("Restart user-mngt POD")
        pods_list = KubernetesPod.get_list()
        user_mngt_pod = next((pod for pod in pods_list if pod.name.startswith(self.POD_NAME_PREFIX)), None)
        assert user_mngt_pod is not None, "POD {} wasn't found on the PODs list".format(self.POD_NAME_PREFIX)
        user_mngt_pod.restart_pod()
        user_mngt_pod.ensure_pod_in_good_health()

        step("Register user with the invitation")
        user = onboarding.register(context=context, code=invitation.code, username=invitation.username)
        assert_user_in_org_and_role(user, Guid.CORE_ORG_GUID, User.ORG_ROLE["user"])
