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

from modules.constants import TapComponent as TAP
from modules.http_calls import platform as api
from modules.markers import priority, components
from modules.runner.tap_test_case import TapTestCase
from tests.fixtures.test_data import TestData


logged_components = (TAP.console,)


@pytest.mark.usefixtures("test_org", "test_org_manager_client", "admin_client")
class AppDevelopmentPage(TapTestCase):
    pytestmark = [components.console]

    @priority.medium
    def test_get_app_development_page(self):
        clients = {"non_admin": TestData.test_org_manager_client, "admin": TestData.admin_client}
        for name, client in clients.items():
            with self.subTest(client=name):
                self.step("Get 'App development' page")
                page = api.api_get_app_development_page(client)
                self.step("Check that header is present")
                self.assertIn("<h3>Tools</h3>", page)
                self.step("Check that url to cloudfoundry documentation is present")
                self.assertIn('<a href="http://docs.cloudfoundry.org/devguide/#cf" target="_blank">', page)
