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
import requests

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import TapComponent as TAP, ServiceCatalogHttpStatus, ServiceLabels, ServicePlan
from modules.markers import incremental, long, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceKey
from tests.fixtures import assertions

logged_components = (TAP.scoring_engine, TAP.service_catalog, TAP.das, TAP.hdfs_downloader,
                     TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.scoring_engine, TAP.service_catalog)]


@pytest.mark.skip(reason="Not yet adjusted to new TAP")
@long
@priority.high
@incremental
@pytest.mark.sample_apps_test
class TestScoringEngineInstance:
    expected_se_bindings = [ServiceLabels.KERBEROS, ServiceLabels.HDFS]

    def test_0_create_instance(self, model_hdfs_path, core_org, core_space, space_users_clients_core, class_context):
        self.__class__.client = space_users_clients_core["developer"]
        step("Create scoring engine instance")
        self.__class__.instance = ServiceInstance.api_create_with_plan_name(
            context=class_context,
            org_guid=core_org.guid,
            space_guid=core_space.guid,
            service_label=ServiceLabels.SCORING_ENGINE,
            service_plan_name=ServicePlan.SIMPLE_ATK,
            params={"uri": model_hdfs_path},
            client=self.client
        )
        step("Check instance is on the instance list")
        instances_list = ServiceInstance.api_get_list(core_space.guid, client=self.client)
        assert self.instance in instances_list, "Scoring Engine was not found on the instance list"

    def test_1_check_service_bindings(self):
        step("Check scoring engine has correct bindings")
        validator = ApplicationStackValidator(self.instance)
        validator.validate(expected_bindings=self.expected_se_bindings)
        self.__class__.se_app = validator.application

    def test_2_check_request_to_se_application(self):
        step("Check that Scoring Engine app responds to an HTTP request")
        url = "http://{}/v1/score?data=10.0,1.5,200.0".format(self.se_app.urls[0])
        headers = {"Accept": "text/plain", "Content-Types": "text/plain; charset=UTF-8"}
        response = requests.post(url, data="", headers=headers)
        assert response.text == "-1.0", "Scoring engine response was wrong"

    def test_3_create_service_key(self, core_space):
        step("Check that the instance exists in summary and has no keys")
        summary = ServiceInstance.api_get_keys(core_space.guid, client=self.client)
        assert self.instance in summary, "Instance not found in summary"
        assert summary[self.instance] == [], "There are keys for the instance"
        step("Create a key for the scoring engine instance and check it")
        self.__class__.instance_key = ServiceKey.api_create(self.instance.guid, client=self.client)
        summary = ServiceInstance.api_get_keys(core_space.guid)
        assert self.instance_key in summary[self.instance], "Key not found"

    def test_4_delete_service_key(self, core_space):
        step("Delete service key")
        self.instance_key.api_delete(client=self.client)
        step("Check the key is no longer in summary")
        summary = ServiceInstance.api_get_keys(core_space.guid, client=self.client)
        assert summary[self.instance] == [], "There are keys for the instance"

    def test_5_delete_instance(self, core_space):
        self.instance.api_delete(client=self.client)
        instances = ServiceInstance.api_get_list(space_guid=core_space.guid)
        assert self.instance not in instances, "Scoring engine instance was not deleted"


@pytest.mark.skip(reason="Not yet adjusted to new TAP")
@priority.low
@pytest.mark.sample_apps_test
class TestScoringEngineUnauthorizedUsers:
    unauthorized_roles = ("manager", "auditor")

    @pytest.mark.parametrize("user_role", unauthorized_roles)
    def test_cannot_create_scoring_engine(self, context, test_org, test_space, space_users_clients, model_hdfs_path, user_role):
        step("Check that unauthorized user cannot create scoring engine")
        client = space_users_clients[user_role]
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_FORBIDDEN,
                                                ServiceCatalogHttpStatus.MSG_FORBIDDEN,
                                                ServiceInstance.api_create_with_plan_name, context=context,
                                                org_guid=test_org.guid, space_guid=test_space.guid,
                                                service_label=ServiceLabels.SCORING_ENGINE,
                                                service_plan_name=ServicePlan.SIMPLE_ATK,
                                                params={"uri": model_hdfs_path}, client=client)
