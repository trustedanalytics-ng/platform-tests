#
# Copyright (c) 2015-2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from modules.constants import TapComponent as TAP, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, priority
from modules.tap_object_model import LatestEvent, Organization, Transfer, User


@log_components()
@components(TAP.latest_events_service)
class DashboardLatestEvents(TapTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.tested_org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.tested_org.guid)
        cls.step("Produce an event in the tested organization - create a data set")
        transfer = Transfer.api_create(org_guid=cls.tested_org.guid, source=Urls.test_transfer_link)
        transfer.ensure_finished()
        cls.step("Create another organization and create a data set in that organization")
        other_org = Organization.api_create()
        cls.step("Add admin to the second organization")
        User.get_admin().api_add_to_organization(org_guid=other_org.guid)
        transfer = Transfer.api_create(org_guid=other_org.guid, source=Urls.test_transfer_link)
        transfer.ensure_finished()
        cls.step("Retrieve latest events from dashboard")
        cls.dashboard_latest_events = LatestEvent.api_get_latest_events_from_org_metrics(cls.tested_org.guid)

    @priority.high
    def test_10_latest_events_on_dashboard_the_same_as_in_LES(self):
        self.step("Retrieve latest events from the LES, filtering with tested organization")
        latest_events_response = LatestEvent.api_get_latest_events(org_guid=self.tested_org.guid)
        self.step("Check that dashboard contains 10 latest events from LES")
        ten_latest_events = sorted(latest_events_response, reverse=True)[:10]
        self.assertUnorderedListEqual(ten_latest_events, self.dashboard_latest_events)
