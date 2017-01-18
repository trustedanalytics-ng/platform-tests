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

from modules.constants import ServicePlan, ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceOffering
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception, assert_not_in_with_retry

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestCreateService:
    APP_TYPE = "JAVA"

    @pytest.fixture(scope="function")
    def offering_json(self):
        return ServiceOffering.create_offering_json()

    @pytest.fixture(scope="class")
    def manifest_json(self):
        return ServiceOffering.create_manifest_json(self.APP_TYPE)

    @priority.low
    @pytest.mark.sample_apps_test
    def test_cannot_create_service_with_no_name(self, context, app_jar,
                                                manifest_json):
        """
        <b>Description:</b>
        Try to create service offering without a name.

        <b>Input data:</b>
        1. jar application
        2. manifest.json file

        <b>Expected results:</b>
        Test passes when platform returns a 402 http status with meaningful message.

        <b>Steps:</b>
        1. Try to create service offering without a name.
        """
        step("Prepare offering json")
        offering_file = ServiceOffering.create_offering_json(name="")
        step("Attempt to create service with empty name")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_SERVICE_NAME_IS_EMPTY,
                                     ServiceOffering.create_from_binary, context, jar_path=app_jar,
                                     manifest_path=manifest_json, offering_path=offering_file)

    @priority.high
    @pytest.mark.sample_apps_test
    def test_create_and_delete_service_offering_admin(self, context, app_jar, offering_json,
                                                      manifest_json, api_service_admin_client):
        """
        <b>Description:</b>
        Create service offering, create an instance of it, delete instance and delete offering.

        <b>Input data:</b>
        1. application jar file
        2. manifest.json file
        3. offering.json file
        4. admin client

        <b>Expected results:</b>
        Test passes when:
        - New offering is created from application jar file.
        - Instance of newly created offering is created.
        - Instance can be deleted.
        - New offering can be deleted from marketplace.

        <b>Steps:</b>
        1. Create service offering from a application jar file.
        2. Create service instance.
        3. Stop service instance.
        4. Delete service instance.
        5. Delete service offering.
        """
        step("Register in marketplace")
        service = ServiceOffering.create_from_binary(context, jar_path=app_jar, manifest_path=manifest_json,
                                                     offering_path=offering_json, client=api_service_admin_client)
        step("Check that service is in marketplace")
        assert_in_with_retry(service, ServiceOffering.get_list)
        step("Check that service is in state 'READY'")
        service.ensure_ready()
        step("Create service instance")
        instance = ServiceInstance.create_with_name(context, offering_label=service.label, plan_name=ServicePlan.FREE)
        step("Check created instance")
        instance.ensure_running()
        assert instance.offering_id == service.id
        assert instance.offering_label == service.label
        step("Stop service instance")
        instance.stop()
        instance.ensure_stopped()
        step("Delete service instance")
        instance.delete()
        instance.ensure_deleted()
        step("Delete service")
        service.delete(client=api_service_admin_client)
        step("Check that service isn't in marketplace")
        assert_not_in_with_retry(service, ServiceOffering.get_list)

    @priority.high
    @pytest.mark.sample_apps_test
    def test_user_cannot_create_service_offering(self, context, app_jar, offering_json,
                                                 manifest_json, test_org_user_client):
        """
        <b>Description:</b>
        Try to create service offering by regular user.

        <b>Input data:</b>
        1. jar application
        2. manifest.json file
        3. user client

        <b>Expected results:</b>
        Test passes when platform returns a 403 http status with meaningful message.

        <b>Steps:</b>
        1. Try to create service offering by regular user.
        """
        step("Register in marketplace")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_FORBIDDEN,
                                     ServiceOffering.create_from_binary, context, jar_path=app_jar,
                                     manifest_path=manifest_json, offering_path=offering_json,
                                     client=test_org_user_client)

    @priority.medium
    @pytest.mark.sample_apps_test
    def test_create_service_with_icon(self, context, app_jar, manifest_json,
                                      example_image):
        """
        <b>Description:</b>
        Create new service offering with custom icon.

        <b>Input data:</b>
        1. application jar file
        2. manifest.json file
        3. example image

        <b>Expected results:</b>
        Test passes when new offering is created with custom icon.

        <b>Steps:</b>
        1. Prepare offering json file with custom icon.
        2. Create service offering.
        3. Check that created offering is present on the offering list.
        4. Check that offering has a custom icon.
        """
        step("Prepare offering json")
        metadata = [{"key": "imageUrl", "value": example_image.decode()}, ]
        offering_file = ServiceOffering.create_offering_json(metadata=metadata)
        step("Register in marketplace")
        service = ServiceOffering.create_from_binary(context, jar_path=app_jar,  manifest_path=manifest_json,
                                                     offering_path=offering_file)
        step("Check that service is in marketplace")
        assert_in_with_retry(service, ServiceOffering.get_list)
        step("Check that images are the same")
        assert example_image == bytes(service.image, "utf8")

    @pytest.mark.bugs("DPNG-14982 Service tags are not supported")
    @priority.medium
    @pytest.mark.sample_apps_test
    def test_create_service_with_tag(self, context, app_jar, manifest_json):
        """
        <b>Description:</b>
        Create new service offering with tag.

        <b>Input data:</b>
        1. application jar file
        2. manifest.json file

        <b>Expected results:</b>
        Test passes when new offering is created with tags.

        <b>Steps:</b>
        1. Prepare offering json file with tags.
        2. Create service offering.
        3. Check that created offering is present on the offering list.
        4. Check that offering has custom tags.
        """
        step("Prepare offering json")
        tags = [generate_test_object_name(short=True)]
        offering_file = ServiceOffering.create_offering_json(tags=tags)
        step("Register in marketplace")
        service = ServiceOffering.create_from_binary(context, jar_path=app_jar, manifest_path=manifest_json,
                                                     offering_path=offering_file)
        step("Check that service is in marketplace")
        assert_in_with_retry(service, ServiceOffering.get_list)
        step("Check that tags names are the same")
        assert tags == service.tags

    @priority.medium
    @pytest.mark.sample_apps_test
    def test_create_service_with_display_name(self, context, app_jar, manifest_json):
        """
        <b>Description:</b>
        Create new service offering with display name.

        <b>Input data:</b>
        1. application jar file
        2. manifest.json file

        <b>Expected results:</b>
        Test passes when new offering is created with display name.

        <b>Steps:</b>
        1. Prepare offering json file with display name.
        2. Create service offering.
        3. Check that created offering is present on the offering list.
        4. Check that offering has custom display name.
        """
        step("Prepare offering json")
        display_name = generate_test_object_name()
        metadata = [{"key": "displayName", "value": display_name}, ]
        offering_file = ServiceOffering.create_offering_json(metadata=metadata)
        step("Register in marketplace")
        service = ServiceOffering.create_from_binary(context, jar_path=app_jar, manifest_path=manifest_json,
                                                     offering_path=offering_file)
        step("Check that service is in marketplace")
        assert_in_with_retry(service, ServiceOffering.get_list)
        step("Check that display names are the same")
        assert display_name == service.display_name
