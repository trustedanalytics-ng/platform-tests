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

from modules.constants import ApiServiceHttpStatus, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceOffering
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.api_service, )
pytestmark = [pytest.mark.components(TAP.api_service)]


class TestApiServiceOfferings:

    @priority.high
    def test_create_and_delete_new_offering(self, context, api_service_admin_client):
        """
        <b>Description:</b>
        Create and later remove offering via api service

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        - It's possible to create offering
        - It's possible to remove the offering

        <b>Steps:</b>
        - Create the offering via api service
        - Verify the offering is on list
        - Verify it's possible to retrieve offering via id
        - Remove the offering
        - Verify the offering was removed
        """
        step("Create new offering")
        test_offering = ServiceOffering.create(context, client=api_service_admin_client)
        step("Check that the new offering is in catalog")
        catalog = ServiceOffering.get_list(client=api_service_admin_client)
        assert test_offering in catalog
        step("Get the offering")
        offering = ServiceOffering.get(offering_id=test_offering.id, client=api_service_admin_client)
        assert test_offering == offering
        step("Delete the offering")
        test_offering.delete(client=api_service_admin_client)
        step("Check that the offering is no longer in catalog")
        catalog = ServiceOffering.get_list(client=api_service_admin_client)
        assert test_offering not in catalog
        step("Check that requesting the deleted offering returns an error")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, ApiServiceHttpStatus.MSG_KEY_NOT_FOUND,
                                     test_offering.delete, client=api_service_admin_client, force=True)

    @priority.low
    def test_cannot_create_the_same_offering_twice(self, context, api_service_admin_client):
        """
        <b>Description:</b>
        Attempts to create offering twice via api service

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        - It's not possible to create the same offering twice

        <b>Steps:</b>
        - Create the offering via api service and verify it's on the list
        - Try to create that offering again
        - Verify that catalog has not changed
        """
        step("Create new offering")
        test_offering = ServiceOffering.create(context, client=api_service_admin_client)
        step("Check that the offering exists")
        catalog = ServiceOffering.get_list(client=api_service_admin_client)
        assert test_offering in catalog
        step("Try creating offering with name of an already existing offering")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_CONFLICT,
                                     ApiServiceHttpStatus.MSG_SERVICE_ALREADY_EXISTS.format(test_offering.label),
                                     ServiceOffering.create, context, label=test_offering.label,
                                     client=api_service_admin_client)
        step("Check that catalog has not changed")
        assert sorted(ServiceOffering.get_list(client=api_service_admin_client)) == sorted(catalog)

