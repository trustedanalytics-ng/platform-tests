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
from modules.constants import ApplicationPath, TapApplicationType, TapComponent as TAP, \
                              UserManagementHttpStatus as HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceOffering
from modules.tap_object_model.prep_app import PrepApp
from tests.fixtures import assertions

logged_components = (TAP.service_catalog, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestTapApp:
    APP_TYPE = "JAVA"

    @pytest.fixture(scope="function")
    def instance(self, context, sample_service):
        step("Create an instance")
        instance = ServiceInstance.create(context, offering_id=sample_service.id,
                                          plan_id=sample_service.service_plans[0]["entity"]["id"])
        step("Ensure that instance is running")
        instance.ensure_running()
        return instance

    @pytest.fixture(scope="function")
    def offering_json(self):
        return ServiceOffering.create_offering_json()

    @pytest.fixture(scope="class")
    def manifest_json(self):
        return ServiceOffering.create_manifest_json(self.APP_TYPE)

    @priority.medium
    @pytest.mark.sample_apps_test
    def test_app_register_as_offering_as_user(self, context, app_jar, offering_json,
                                              manifest_json, test_user_clients):
        """
        <b>Description:</b>
        Checks if an offering can be created from an application.

        <b>Input data:</b>
        1. Sample application.
        2. Organization id

        <b>Expected results:</b>
        An offering CAN'T be created from an application as user

        <b>Steps:</b>
        1. Try to create offering and fail.
        """
        client = test_user_clients["user"]
        step("Register in marketplace as user")
        assertions.assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN,
                                                HttpStatus.MSG_FORBIDDEN,
                                                ServiceOffering.create_from_binary,
                                                context, jar_path=app_jar,
                                                manifest_path=manifest_json,
                                                offering_path=offering_json,
                                                client=client)

