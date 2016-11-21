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

from modules.constants import CatalogHttpStatus, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogService
from modules.tap_object_model._service_plan import ServicePlan
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.catalog,)
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogServicePlans:

    @pytest.fixture(scope="class")
    def catalog_service(self, class_context, catalog_template):
        log_fixture("Create sample catalog service")
        return CatalogService.create(class_context, template_id=catalog_template.id)

    def plan_body(self):
        return {
            "name": "add_plan_to_service",
            "description": "plan_test",
            "cost": "free"
        }

    def create_plan_for_service(self, service):
        step("Create plan for service")
        return service.create_plan(self.plan_body())

    @priority.high
    def test_get_service_plan_list(self, catalog_service):
        step("Get service plan list")
        plans = ServicePlan.get_plans(service_id=catalog_service.id)
        assert len(plans) == 1

    @priority.low
    def test_get_service_plan_list_with_invalid_service_id(self):
        step("Get service plan list with invalid service id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     ServicePlan.get_plans, service_id=generate_test_object_name())

    @priority.high
    def test_create_service_without_plans(self, context, catalog_template):
        step("Create service without plans")
        catalog_service = CatalogService.create(context, template_id=catalog_template.id, plans=[])
        plans = ServicePlan.get_plans(service_id=catalog_service.id)
        assert len(plans) == 0

        step("Create plan for service without plans")
        self.create_plan_for_service(catalog_service)
        plans = ServicePlan.get_plans(service_id=catalog_service.id)
        assert len(plans) == 1

        step("Create another plan for service")
        service_plan_body = self.plan_body()
        service_plan_body["name"] = "add_plan_to_service2"
        plan = catalog_service.create_plan(service_plan_body)
        plans = ServicePlan.get_plans(service_id=catalog_service.id)
        assert len(plans) == 2

        step("Create another plan for service with id filled")
        service_plan_body["id"] = "test"
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_ID_HAS_TO_BE_EMPTY,
                                     catalog_service.create_plan, body=service_plan_body)

        step("Get created service plan")
        retrieved_plan = ServicePlan.get_plan(service_id=catalog_service.id, plan_id=plan.id)
        assert plan == retrieved_plan

    @priority.low
    def test_get_service_plan_by_invalid_plan_id(self, catalog_service):
        step("Get service plan by invalid plan id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     ServicePlan.get_plan, service_id=catalog_service.id,
                                     plan_id=generate_test_object_name())

    @priority.high
    def test_update_plan(self, catalog_service):
        step("Update existing plan")
        plan = self.create_plan_for_service(catalog_service)
        updated_plan = ServicePlan.update_plan(service_id=catalog_service.id, plan_id=plan.id,
                                               field="description", value="plan_test_update")
        assert updated_plan.description == "plan_test_update"

    @priority.low
    def test_update_plan_with_invalid_plan_id(self, catalog_service):
        step("Update plan using invalid plan id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     ServicePlan.update_plan, service_id=catalog_service.id,
                                     plan_id=generate_test_object_name(),
                                     field="description", value="plan_test_update")

    @priority.low
    def test_delete_not_existing_service_plan(self, catalog_service):
        step("Delete not existing service plan")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     ServicePlan.delete_plan, service_id=catalog_service.id,
                                     plan_id=generate_test_object_name())

    @priority.high
    def test_delete_plan(self, catalog_service):
        step("Delete service plan")
        plan = self.create_plan_for_service(catalog_service)
        ServicePlan.delete_plan(service_id=catalog_service.id, plan_id=plan.id)

        step("Delete the same service plan again")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     ServicePlan.delete_plan, service_id=catalog_service.id, plan_id=plan.id)

        step("Get removed service plan")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     ServicePlan.get_plan, service_id=catalog_service.id, plan_id=plan.id)
