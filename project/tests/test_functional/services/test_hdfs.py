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

from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_type import HttpClientType
from modules.http_client.config import Config
from modules.markers import components, incremental ,priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceKey
from modules.tap_object_model.flows import services
from tests.fixtures import assertions


logged_components = (TAP.hdfs_broker,)
pytestmark = [components.hdfs_broker]


label = ServiceLabels.HDFS
special_plan_names = [ServicePlan.CREATE_USER_DIRECTORY, ServicePlan.GET_USER_DIRECTORY]


@pytest.fixture(scope="module")
def hdfs_service_offering(test_marketplace):
    hdfs = next((s for s in test_marketplace if s.label == label), None)
    assert hdfs is not None, "{} service was not found".format(label)
    return hdfs


class TestHdfsRegularPlans(object):

    @priority.high
    def test_create_hdfs_service_instance_and_keys(self, test_org, test_space, hdfs_service_offering):
        failures = []
        for plan in hdfs_service_offering.service_plans:
            if plan["name"] in special_plan_names:
                continue
            try:
                step("Testing service {} plan {}".format(label, plan["name"]))
                services.create_instance_and_key_then_delete_key_and_instance(
                    org_guid=test_org.guid,
                    space_guid=test_space.guid,
                    service_label=label,
                    plan_guid=plan["guid"],
                    plan_name=plan["name"]
                )
            except Exception as e:
                failures.append("{}\n{}".format(plan["guid"], e))
        assertions.assert_no_errors(failures)

        assert len(failures) == 0, "The following items failed:\n{}".format("\n".join(failures))


@incremental
@priority.medium
class TestHdfsUserDirectoryPlans(object):

    def test_0_hdfs_create_user_directory_instance(self, test_org, test_space, add_admin_to_test_org,
                                                   add_admin_to_test_space, hdfs_service_offering):
        step("Create {} instance with {} plan".format(label, ServicePlan.CREATE_USER_DIRECTORY))
        create_directory_plan_guid = next((p["guid"] for p in hdfs_service_offering.service_plans
                                           if p["name"] == ServicePlan.CREATE_USER_DIRECTORY), None)
        assert create_directory_plan_guid is not None,\
            "Plan with name {} for service {} not found".format(ServicePlan.CREATE_USER_DIRECTORY, label)
        self.__class__.instance_cud = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=label,
            service_plan_guid=create_directory_plan_guid
        )
        self.instance_cud.ensure_created()

    def test_1_hdfs_key_for_create_user_directory_instance(self):
        step("Create service key for the instance and check required keys are present")
        self.__class__.key = ServiceKey.api_create(service_instance_guid=self.instance_cud.guid)
        assert "uri" in self.key.credentials
        assert "user" in self.key.credentials
        assert "password" in self.key.credentials

    def test_2_hdfs_check_uaa_credentials_are_correct(self):
        step("Check that uaa token can be retrieved using credentials from the service key")
        username = self.key.credentials["user"]
        password = self.key.credentials["password"]
        uaa_client_configuration = HttpClientConfiguration(client_type=HttpClientType.UAA, url=Config.service_uaa_url(),
                                                           username=username, password=password)
        HttpClientFactory.get(uaa_client_configuration).request(method=HttpMethod.GET, path="", msg="UAA: test request")

    def test_3_hdfs_get_user_directory_instance(self, test_org, test_space, hdfs_service_offering):
        step("Create {} instance with {} plan".format(ServiceLabels.HDFS, ServicePlan.GET_USER_DIRECTORY))
        uri = self.key.credentials["uri"]
        get_directory_plan_guid = next((p["guid"] for p in hdfs_service_offering.service_plans
                                        if p["name"] == ServicePlan.GET_USER_DIRECTORY), None)
        assert get_directory_plan_guid is not None,\
            "Plan with name {} for service {} not found".format(ServicePlan.GET_USER_DIRECTORY, label)
        self.__class__.instance_gud = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=label,
            service_plan_guid=get_directory_plan_guid,
            params={"uri": uri}
        )
        self.instance_gud.ensure_created()

    def test_4_hdfs_delete_key_and_instances(self):
        step("Delete {} instance with plan {}".format(label, ServicePlan.GET_USER_DIRECTORY))
        self.instance_gud.api_delete()
        step("Delete key for {} {}".format(label, ServicePlan.CREATE_USER_DIRECTORY))
        self.key.api_delete()
        step("Delete {} instance with plan {}".format(label, ServicePlan.CREATE_USER_DIRECTORY))
        self.instance_cud.api_delete()
