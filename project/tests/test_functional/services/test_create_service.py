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

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceOffering
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception, assert_not_in_with_retry

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog),
              pytest.mark.skip(reason="DPNG-11125 api-service: endpoint for adding offerings from jar archives")]


@priority.low
@pytest.mark.sample_apps_test
def test_cannot_create_service_with_no_name(context, test_org):
    step("Attempt to create service with empty name")
    assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                 ServiceOffering.create_from_binary, context, org_guid=test_org.guid, service_name="")


@priority.low
@pytest.mark.sample_apps_test
def test_cannot_create_service_with_no_description(context, test_org):
    step("Attempt to create service with empty description")
    assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                 ServiceOffering.create_from_binary, context, org_guid=test_org.guid,
                                 service_description="")


@priority.high
@pytest.mark.sample_apps_test
@pytest.mark.parametrize("role", ["admin", "user"])
def test_create_and_delete_service_offering(context, test_org, test_user_clients, role):
    client = test_user_clients[role]
    step("Register in marketplace")
    service = ServiceOffering.create_from_binary(context, org_guid=test_org.guid, client=client)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceOffering.get_list)
    step("Delete service")
    service.api_delete(client=client)
    step("Check that service isn't in marketplace")
    assert_not_in_with_retry(service, ServiceOffering.get_list)


@priority.medium
@pytest.mark.sample_apps_test
def test_create_service_with_icon(context, test_org, example_image):
    step("Register in marketplace")
    service = ServiceOffering.create_from_binary(context, org_guid=test_org.guid, image=example_image)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceOffering.get_list)
    step("Check that images are the same")
    assert example_image == bytes(service.image, "utf8")


@priority.medium
@pytest.mark.sample_apps_test
def test_create_service_with_display_name(context, test_org):
    display_name = generate_test_object_name()
    step("Register in marketplace")
    service = ServiceOffering.create_from_binary(context, org_guid=test_org.guid, display_name=display_name)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceOffering.get_list)
    step("Check that display names are the same")
    assert display_name == service.display_name


@priority.medium
@pytest.mark.sample_apps_test
def test_create_service_with_tag(context, test_org):
    tags = [generate_test_object_name(short=True)]
    step("Register in marketplace")
    service = ServiceOffering.create_from_binary(context, org_guid=test_org.guid, tags=tags)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceOffering.get_list)
    step("Check that tags names are the same")
    assert tags == service.tags
