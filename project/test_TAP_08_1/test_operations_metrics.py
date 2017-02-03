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

import pytest

from config import console_url
from modules.constants import HttpStatus, TapComponent as TAP
from modules.tap_logger import step
from modules.tap_object_model import Metrics, User
from tests.fixtures import assertions
from modules.http_client.client_auth.http_method import HttpMethod

logged_components = (TAP.platform_operations, )
pytestmark = [pytest.mark.components(TAP.platform_operations)]


class TestNonAdminOperationsMetrics:
    PLATFORM_SUMMARY_PATH = "app/operations/platformdashboard/platform-summary.html"

    #@pytest.mark.bugs("DPNG-15270 non-admin user receives summary page layout")
    def test_non_admin_cannot_access_platform_operations(self, context, test_org):
        """
        <b>Description:</b>
        Checks if non-admin user cannot reach summary operations page /app/platformdashboard/summary.

        <b>Input data:</b>
        1. User email.

        <b>Expected results:</b>
        Test passes when non-admin user was not able to reach summary operations page.

        <b>Steps:</b>
        1. Create non-admin user.
        2. Verify that the user cannot reach summary operations page.
        """
        step("Create non-admin user")
        test_user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid)
        client = test_user.login(rest_prefix="")
        step("Checking if non-admin user cannot request admin-only data")
        assertions.assert_raises_http_exception(HttpStatus.CODE_UNAUTHORIZED, HttpStatus.MSG_UNAUTHORIZED,
                                                client.request, method=HttpMethod.GET, url=console_url,
                                                path=self.PLATFORM_SUMMARY_PATH)


