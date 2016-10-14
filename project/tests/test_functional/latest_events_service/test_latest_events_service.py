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

from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP, Urls
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, EventCategory, EventMessage, LatestEvent, Organization, ServiceInstance,\
    Space, Transfer


logged_components = (TAP.latest_events_service, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.latest_events_service)]


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 (DPNG-8720)")
class TestLatestEventsService:

    @pytest.fixture(scope="class")
    def org(self, class_context):
        return Organization.api_create(class_context)

    @pytest.fixture(scope="class")
    def space(self, org):
        return Space.api_create(org=org)

    @pytest.fixture(scope="function")
    def events_before(self, org):
        step("Retrieve latest events from the test org")
        return LatestEvent.api_get_latest_events(org_guid=org.guid)

    @staticmethod
    def _assert_event_is_correct(tested_event, category, message, org_guid):
        assert category == tested_event.category.strip()
        assert message == tested_event.message.strip()
        assert org_guid == tested_event.org_id

    @priority.medium
    def test_data_catalog_events(self, org, admin_user, events_before, context):
        step("Add admin to test org")
        admin_user.api_add_to_organization(org_guid=org.guid)
        step("Produce an event in the test org - create a dataset")
        transfer = Transfer.api_create(context, org_guid=org.guid, source=Urls.test_transfer_link)
        transfer.ensure_finished()
        step("Ensure that a dataset has been created")
        data_set = DataSet.api_get_matching_to_transfer(transfer_title=transfer.title, org_guid=org.guid)
        step("Retrieve latest events. Check that there is one new event related to dataset creation.")
        events_after_create = LatestEvent.api_get_latest_events(org_guid=org.guid)
        assert len(events_after_create) == len(events_before) + 1
        self._assert_event_is_correct(events_after_create[0], category=EventCategory.data_catalog, org_guid=org.guid,
                                      message=EventMessage.dataset_added.format(Urls.test_transfer_link))
        step("Produce an event in the test org - delete the dataset")
        data_set.api_delete()
        step("Retrieve latest events. Check that there is one new event related to dataset creation.")
        events_after_delete = LatestEvent.api_get_latest_events(org_guid=org.guid)
        assert len(events_after_delete) == len(events_after_create) + 1
        self._assert_event_is_correct(events_after_delete[0], category=EventCategory.data_catalog, org_guid=org.guid,
                                      message=EventMessage.dataset_deleted.format(Urls.test_transfer_link))

    @priority.medium
    def test_failed_instance_creation_event(self, context, org, space, events_before):
        step("Trigger failed instance creation")
        with pytest.raises(AssertionError):
            ServiceInstance.api_create_with_plan_name(context, org.guid, space.guid, ServiceLabels.SCORING_ENGINE,
                                                      service_plan_name=ServicePlan.SIMPLE_ATK)
        step("Retrieve latest events. Check there are two new events related to failed instance creation")
        events_after = LatestEvent.api_get_latest_events(org_guid=org.guid)
        assert len(events_after) == len(events_before) + 2
        self._assert_event_is_correct(events_after[1], category=EventCategory.service_creation, org_guid=org.guid,
                                      message=EventMessage.create_service_started.format(Urls.test_transfer_link))
        self._assert_event_is_correct(events_after[0], category=EventCategory.service_creation, org_guid=org.guid,
                                      message=EventMessage.create_service_failed.format(Urls.test_transfer_link))

    @priority.medium
    def test_successful_instance_creation_event(self, context, org, space, events_before):
        step("Create example instance")
        ServiceInstance.api_create_with_plan_name(context, org.guid, space.guid, ServiceLabels.ATK,
                                                  service_plan_name=ServicePlan.SIMPLE_ATK)
        step("Retrieve latest events. Check there are two new events related to successful instance creation")
        events_after = LatestEvent.api_get_latest_events(org_guid=org.guid)
        assert len(events_after) == len(events_before) + 2
        self._assert_event_is_correct(events_after[1], category=EventCategory.service_creation, org_guid=org.guid,
                                      message=EventMessage.create_service_started.format(Urls.test_transfer_link))
        self._assert_event_is_correct(events_after[0], category=EventCategory.service_creation, org_guid=org.guid,
                                      message=EventMessage.create_service_succeded)
