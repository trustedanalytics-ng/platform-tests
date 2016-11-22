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

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP, ServiceLabels
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceOffering
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


@priority.medium
class TestDeleteService:

    @pytest.fixture(scope="class")
    def public_service(self):
        services = ServiceOffering.get_list()
        return next(s for s in services if s.label == ServiceLabels.ZOOKEEPER)

    @pytest.mark.skip(reason="DPNG-12855 Deleting service broker offering - not yet implemented")
    @pytest.mark.parametrize("role", ["user"])
    def test_cannot_delete_public_service_as_non_admin(self, test_user_clients, role, public_service):
        client = test_user_clients[role]
        step("Attempt to delete public service")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_USER_NOT_AUTHORIZED_TO_DELETE_SERVICE,
                                     public_service.delete, client=client)

    @pytest.mark.skip(reason="DPNG-11414 Create offering from binary - not supported yet")
    @pytest.mark.parametrize("role", ["admin"])
    def test_cannot_remove_service_with_instance(self, context, sample_service, test_user_clients, role):
        client = test_user_clients[role]
        offering_id = sample_service.id
        plan_id = sample_service.service_plans[0].id

        step("Create an instance")
        instance = ServiceInstance.create(context, offering_id=offering_id, plan_id=plan_id, client=client)

        step("Ensure that instance is running")
        instance.ensure_running()

        step("Check that service instance is present")
        assert_in_with_retry(instance, ServiceInstance.get_list, name=instance.name)

        step("Attempt to delete public service with instnace")
        assert_raises_http_exception(HttpStatus.CODE_INTERNAL_SERVER_ERROR,
                                     HttpStatus.MSG_CANNOT_REMOVE_SERVICE_WITH_INSTANCE,
                                     sample_service.delete)
