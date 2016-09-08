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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import LatestEvent, Organization, Transfer, User
from tests.fixtures.assertions import assert_unordered_list_equal

logged_components = (TAP.latest_events_service,)
pytestmark = [pytest.mark.components(TAP.latest_events_service)]


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 (DPNG-8720)")
@pytest.mark.usefixtures("add_admin_to_test_org")
class TestDashboardLatestEvents:

    @pytest.fixture(scope="function")
    def another_org(self, context):
        step("Create another test organization")
        another_org = Organization.api_create(context)
        return another_org

    @pytest.fixture(scope="function")
    def another_org_client(self, context, another_org):
        step("Create org manager in another org")
        user = User.api_create_by_adding_to_organization(org_guid=another_org.guid, context=context)
        return user.login()

    @priority.high
    def test_10_latest_events_on_dashboard_the_same_as_in_LES(self, context, test_org, test_data_urls):
        step("Produce an event in the tested organization - create a data set")
        transfer = Transfer.api_create(context, org_guid=test_org.guid, source=test_data_urls.test_transfer.url)
        transfer.ensure_finished()
        step("Retrieve latest events from dashboard")
        dashboard_latest_events = LatestEvent.api_get_latest_events_from_org_metrics(test_org.guid)
        step("Retrieve latest events from the LES, filtering with tested organization")
        latest_events_response = LatestEvent.api_get_latest_events(test_org.guid)
        step("Check that dashboard contains 10 latest events from LES")
        ten_latest_events = sorted(latest_events_response, reverse=True)[:10]
        assert_unordered_list_equal(ten_latest_events, dashboard_latest_events)

    @priority.low
    def test_visibility_of_events(self, test_org, context, test_org_manager_client, test_data_urls):
        events_before = LatestEvent.api_get_latest_events_from_org_metrics(test_org.guid)
        step("Create dataset by admin")
        transfer = Transfer.api_create(context, org_guid=test_org.guid, source=test_data_urls.test_transfer.url)
        transfer.ensure_finished()
        events_after = LatestEvent.api_get_latest_events_from_org_metrics(test_org.guid)
        step("Check admin dataset creation event is visible")
        assert len(events_before) + 1 == len(events_after)
        step("Create dataset by non-admin user")
        transfer = Transfer.api_create(context, org_guid=test_org.guid, source=test_data_urls.test_transfer.url,
                                       client=test_org_manager_client)
        transfer.ensure_finished()
        events_after = LatestEvent.api_get_latest_events_from_org_metrics(test_org.guid, client=test_org_manager_client)
        step("Check that non-admin dataset creation event is visible")
        assert len(events_before) + 2 == len(events_after)

    @priority.low
    def test_events_visibility_from_another_org(self, test_org, context, another_org, another_org_client, test_data_urls):
        events_before = LatestEvent.api_get_latest_events_from_org_metrics(another_org.guid, client=another_org_client)
        step("Create dataset in another org")
        transfer = Transfer.api_create(context, org_guid=another_org.guid, source=test_data_urls.test_transfer.url,
                                       client=another_org_client)
        transfer.ensure_finished()
        step("Check event is on the latest events list")
        events_after = LatestEvent.api_get_latest_events_from_org_metrics(another_org.guid, client=another_org_client)
        assert len(events_before) + 1 == len(events_after), "The new event is not visible"
        step("Check events from one org are not visible in another org")
        test_org_events = LatestEvent.api_get_latest_events_from_org_metrics(test_org.guid)
        assert all((event not in test_org_events for event in events_after)), \
            "Some events from the another org are visible in first org"
