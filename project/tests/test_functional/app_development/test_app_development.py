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

from modules.constants import TapComponent as TAP
from modules.http_calls.platform import platform_pages as api
from modules.markers import components
from modules.tap_logger import step

logged_components = (TAP.console,)


class TestAppDevelopmentPage(object):
    pytestmark = [components.console]

    def test_get_app_development_page(self, admin_client, test_org_manager_client):
        self._assert_app_development_page(admin_client)
        self._assert_app_development_page(test_org_manager_client)

    @staticmethod
    def _assert_app_development_page(client):
        step("Get 'App development' page")
        page = api.api_get_app_development_page(client)
        step("Check that header is present")
        assert "<h3>Tools</h3>" in page
        step("Check that url to cloudfoundry documentation is present")
        assert '<a href="http://docs.cloudfoundry.org/devguide/#cf" target="_blank">' in page
