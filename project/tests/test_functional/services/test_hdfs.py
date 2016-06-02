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
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceKey
from modules.tap_object_model.flows import services
from tests.fixtures import assertions


logged_components = (TAP.hdfs_broker,)
pytestmark = [components.hdfs_broker]


class TestHdfsService(object):
    label = ServiceLabels.HDFS
    special_plan_names = [ServicePlan.CREATE_USER_DIRECTORY, ServicePlan.GET_USER_DIRECTORY]

    @pytest.fixture(scope="class")
    def hdfs_service_offering(self, test_marketplace):
        hdfs = next((s for s in test_marketplace if s.label == self.label), None)
        assert hdfs is not None, "{} service was not found".format(self.label)
        return hdfs

    @priority.high
    def test_create_hdfs_service_instance_and_keys(self, test_org, test_space, hdfs_service_offering):
        failures = []
        for plan in hdfs_service_offering.service_plans:
            if plan["name"] in self.special_plan_names:
                continue
            try:
                step("Testing service {} plan {}".format(self.label, plan["name"]))
                services.create_instance_and_key_then_delete_key_and_instance(
                    org_guid=test_org.guid,
                    space_guid=test_space.guid,
                    service_label=self.label,
                    plan_guid=plan["guid"],
                    plan_name=plan["name"]
                )
            except Exception as e:
                failures.append("{}\n{}".format(plan["guid"], e))
        assertions.assert_no_errors(failures)

        assert len(failures) == 0, "The following items failed:\n{}".format("\n".join(failures))

    @priority.medium
    def test_create_and_delete_hdfs_service_user_directory_plans(self, test_org, test_space, add_admin_to_test_org,
                                                                 add_admin_to_test_space, hdfs_service_offering):
        step("Create {} instance with {} plan".format(self.label, ServicePlan.CREATE_USER_DIRECTORY))
        create_directory_plan_guid = next((p["guid"] for p in hdfs_service_offering.service_plans
                                           if p["name"] == ServicePlan.CREATE_USER_DIRECTORY), None)
        assert create_directory_plan_guid is not None,\
            "Plan with name {} for service {} not found".format(ServicePlan.CREATE_USER_DIRECTORY, self.label)
        instance_1 = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=self.label,
            service_plan_guid=create_directory_plan_guid
        )
        instance_1.ensure_created()

        step("Create service key for the instance")
        key = ServiceKey.api_create(service_instance_guid=instance_1.guid)
        assert "uri" in key.credentials
        assert "user" in key.credentials
        assert "password" in key.credentials

        uri = key.credentials["uri"]

        step("Create {} instance with {} plan".format(ServiceLabels.HDFS, ServicePlan.GET_USER_DIRECTORY))
        get_directory_plan_guid = next((p["guid"] for p in hdfs_service_offering.service_plans
                                        if p["name"] == ServicePlan.GET_USER_DIRECTORY), None)
        assert create_directory_plan_guid is not None,\
            "Plan with name {} for service {} not found".format(ServicePlan.GET_USER_DIRECTORY, self.label)
        instance_2 = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=self.label,
            service_plan_guid=get_directory_plan_guid,
            params={"uri": uri}
        )
        instance_2.ensure_created()

        step("Delete {} instance with plan {}".format(self.label, ServicePlan.GET_USER_DIRECTORY))
        instance_2.api_delete()
        step("Delete key for {} {}".format(self.label, ServicePlan.CREATE_USER_DIRECTORY))
        key.api_delete()
        step("Delete {} instance with plan {}".format(self.label, ServicePlan.CREATE_USER_DIRECTORY))
        instance_1.api_delete()
