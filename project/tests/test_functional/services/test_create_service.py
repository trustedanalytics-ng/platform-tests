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

from modules.constants import ServicePlan, ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP, Urls
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceOffering
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception, assert_not_in_with_retry

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestCreateService:
    SAMPLE_APP_URL = Urls.tapng_java_app_url
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
        step("Prepare offering json")
        offering_file = ServiceOffering.create_offering_json(name="")
        step("Attempt to create service with empty name")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_SERVICE_NAME_IS_EMPTY,
                                     ServiceOffering.create_from_binary, context, jar_path=app_jar,
                                     manifest_path=manifest_json, offering_path=offering_file)

    @priority.high
    @pytest.mark.sample_apps_test
    @pytest.mark.parametrize("role", ["admin", "user"])
    @pytest.mark.bugs("DPNG-13211 api-service responses don't relate to swagger definition")
    def test_create_and_delete_service_offering(self, context, app_jar, offering_json,
                                                manifest_json, test_user_clients, role):
        client = test_user_clients[role]
        step("Register in marketplace")
        service = ServiceOffering.create_from_binary(context, jar_path=app_jar, manifest_path=manifest_json,
                                                     offering_path=offering_json, client=client)
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
        service.delete(client=client)
        step("Check that service isn't in marketplace")
        assert_not_in_with_retry(service, ServiceOffering.get_list)

    @priority.medium
    @pytest.mark.sample_apps_test
    def test_create_service_with_icon(self, context, app_jar, manifest_json,
                                      example_image):
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

    @priority.medium
    @pytest.mark.sample_apps_test
    @pytest.mark.bugs("DPNG-12742 /v2/api/offerings in tap-api-service does not return Service name and Metadata")
    def test_create_service_with_tag(self, context, app_jar, manifest_json):
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
