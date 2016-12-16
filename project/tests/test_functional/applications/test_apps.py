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
from modules.tap_object_model.prep_app import PrepApp
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
        """
        <b>Description:</b>
        Checks if different type of users can do the application flow.

        <b>Input data:</b>
        1. Username.
        2. User password.
        3. Sample java application.

        <b>Expected results:</b>
        Different users can do an application flow.

        <b>Steps:</b>
        1. Push an application.
        2. Verify is running.
        3. Verify can be stopped.
        4. Verify can be started.
        5. Verify can be restarted.
        6. Verify can be deleted.
        7. Verify is doesn't exist.
        """
        client = test_user_clients[role]

        step("Compile the app")
        test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
        test_app_sources.compile_mvn()

        step("Package the app")
        p_a = PrepApp(ApplicationPath.SAMPLE_JAVA_APP)
        gzipped_app_path = p_a.package_app(context)

        step("Update manifest")
        manifest_params = {"type" : TapApplicationType.JAVA}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push app to tap")
        app = Application.push(context, app_path=gzipped_app_path,
                               name=p_a.app_name, manifest_path=manifest_path,
                               client=client)

        step("Check the application is running")
        app.ensure_running()
        step("Stop the application and check that it is stopped")
        app.stop()
        app.ensure_stopped()
        step("Start the application and check that it has started")
        app.start()
        app.ensure_running()
        step("Restart the application and check that it's running")
        app.restart()
        app.ensure_running()
        step("Stop application before delete")
        app.stop()
        app.ensure_stopped()
        step("Delete the application and check that it doesn't exist")
        app.delete()
        assertions.assert_not_in_by_id_with_retry(app.id, Application.get_list)

    @pytest.mark.skip(reason="DPNG-11414 Create offering from binary - not supported yet")
    @priority.medium
    @pytest.mark.sample_apps_test
    def test_app_register_as_offering(self, context, test_org):
        """
        <b>Description:</b>
        Checks if an offering can be created from an application.

        <b>Input data:</b>
        1. Sample application.
        2. Organization id

        <b>Expected results:</b>
        An offering can be created from an application.

        <b>Steps:</b>
        1. Create offering.
        2. Verify is on the offerings list.
        """
        register_offering = ServiceOffering.create_from_binary(context, org_guid=test_org.guid)
        register_offering.ensure_ready()
        assertions.assert_in_with_retry(register_offering, ServiceOffering.get_list)

    @pytest.mark.skip(reason="DPNG-12190 cascade flag is not supported yet")
    @priority.medium
    def test_cascade_app_delete(self, context, instance, admin_client):
        """
        <b>Description:</b>
        Checks if cascade removal of an application removes bound service instance too.

        <b>Input data:</b>
        1. Sample service instance.
        2. Sample java application.
        3. Admin client

        <b>Expected results:</b>
        The application and the service instance are deleted.

        <b>Steps:</b>
        1. Push an application with bound service instance.
        2. Verify the application is running.
        3. Delete the application with cascade flag.
        4. Verify the application is deleted.
        5. Verify the service instance is deleted.
        """
        step("Compile the app")
        test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
        test_app_sources.compile_mvn()

        step("Package the app")
        p_a = PrepApp(ApplicationPath.SAMPLE_JAVA_APP)
        gzipped_app_path = p_a.package_app(context)

        step("Update manifest")
        manifest_params = {"type" : TapApplicationType.JAVA,
                           "bindings" : instance.id}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push app to tap")
        app = Application.push(context, app_path=gzipped_app_path,
                               name=p_a.app_name, manifest_path=manifest_path,
                               client=admin_client)
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
        """
        <b>Description:</b>
        Checks if an application can be deleted.

        <b>Input data:</b>
        1. Sample java application.

        <b>Expected results:</b>
        The application doesn't exist.

        <b>Steps:</b>
        1. Stop the application.
        2. Verify is stopped.
        3. Delete the application.
        4. Verify is doesn't exist.
        """
        step("Stop application")
        sample_java_app.stop()
        sample_java_app.ensure_stopped()
        step("Delete the application and check that it doesn't exist")
        sample_java_app.delete()
        assertions.assert_not_in_by_id_with_retry(sample_java_app.id, Application.get_list)
