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
from modules.tap_object_model import Application, ServiceInstance
from modules.tap_object_model.prep_app import PrepApp
from tests.fixtures import assertions

logged_components = (TAP.service_catalog, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestTapApp:

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
