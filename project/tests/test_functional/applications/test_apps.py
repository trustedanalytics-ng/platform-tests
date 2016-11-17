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

from modules.app_sources import AppSources
from modules.constants import ApplicationPath, TapApplicationType, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceOffering
from tests.fixtures import assertions


logged_components = (TAP.service_catalog, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestTapApp:

    @pytest.fixture(scope="function")
    def instance(self, context, sample_service):
        step("Create an instance")
        instance = ServiceInstance.create(context, offering_id=sample_service.id,
                                          plan_id=sample_service.service_plans[0]["entity"]["id"])
        step("Ensure that instance is running")
        instance.ensure_running()
        return instance

    @pytest.mark.bugs("DPNG-12584 'Cannot parse ApiServiceInstance list: key PLAN_ID not found!' "
                      "after trying to check Marketplace->Services and details of applications.")
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_user_can_do_app_flow(self, test_user_clients, role, context):
        client = test_user_clients[role]

        test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
        test_app_sources.compile_mvn()
        step("Push app to tap")
        app = Application.push(context, app_path=ApplicationPath.SAMPLE_JAVA_APP,
                               client=client, app_type=TapApplicationType.JAVA)
        step("Check the application is running")
        app.ensure_running()
        step("Stop the application and check that it is stopped")
        app.stop()
        app.ensure_stopped()
        step("Start the application and check that it has started")
        app.start()
        app.ensure_running()
        step("Delete the application and check that it doesn't exist")
        app.delete()
        assertions.assert_not_in_by_id_with_retry(app.id, Application.get_list)

    @pytest.mark.skip(reason="DPNG-11414 Create offering from binary - not supported yet")
    @priority.medium
    @pytest.mark.sample_apps_test
    def test_app_register_as_offering(self, context, test_org):
        register_offering = ServiceOffering.create_from_binary(context, org_guid=test_org.guid)
        register_offering.ensure_ready()
        assertions.assert_in_with_retry(register_offering, ServiceOffering.get_list)

    @pytest.mark.skip(reason="DPNG-12190 cascade flag is not supported yet")
    @priority.medium
    def test_cascade_app_delete(self, context, instance, admin_client):
        test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
        test_app_sources.compile_mvn()
        step("Push app to tap")
        app = Application.push(context, app_path=ApplicationPath.SAMPLE_JAVA_APP,
                               client=admin_client, app_type=TapApplicationType.JAVA,
                               bindings=[instance.id])
        step("Check the application is running")
        app.ensure_running()

        app.api_delete(cascade=True)
        assertions.assert_not_in_by_id_with_retry(app.id, Application.get_list)
        assertions.assert_not_in_by_id_with_retry(instance.id, ServiceInstance.get_list)

    @pytest.mark.bugs("DPNG-12584 'Cannot parse ApiServiceInstance list: key PLAN_ID not found!' "
                      "after trying to check Marketplace->Services and details of applications.")
    @priority.medium
    @pytest.mark.sample_apps_test
    def test_delete_app(self, sample_java_app):
        step("Delete the application and check that it doesn't exist")
        sample_java_app.delete()
        assertions.assert_not_in_by_id_with_retry(sample_java_app.id, Application.get_list)
