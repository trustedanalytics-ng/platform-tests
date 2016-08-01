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
from modules.http_calls import cloud_foundry as cf
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, ServiceInstance, Space
from modules.tap_object_model.flows.summaries import cf_api_get_space_summary

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestTapServiceInstance:
    @pytest.fixture(scope="function")
    def org_space(self, context):
        step("Create test organization and space")
        test_org = Organization.api_create(context)
        test_space = Space.api_create(test_org)
        return test_org, test_space

    @pytest.fixture(scope="function")
    def instance(self, context, org_space):
        instance = ServiceInstance.api_create_with_plan_name(context=context,
                                                             org_guid=org_space[0].guid, space_guid=org_space[1].guid,
                                                             service_label=ServiceLabels.KAFKA,
                                                             service_plan_name=ServicePlan.SHARED)
        return instance

    @priority.medium
    def test_compare_service_instances_list_with_cf(self, org_space, instance):
        test_org, test_space = org_space
        step("Get service instances list from platform")
        platform_service_instances_list = ServiceInstance.api_get_list(test_space.guid)
        step("Get service instances list from cf")
        cf_service_instances_list = ServiceInstance.cf_api_get_list()
        cf_service_instances_list = [s for s in cf_service_instances_list if s.space_guid == org_space[1].guid]
        assert instance in platform_service_instances_list
        cf_service_guids = [s.guid for s in cf_service_instances_list]
        platform_service_guids = [s.guid for s in platform_service_instances_list]
        step("Compare service instances lists from platform and cf")
        assert cf_service_guids == platform_service_guids

    @priority.medium
    def test_create_service_instance(self, org_space, instance):
        test_org, test_space = org_space
        step('Login to cf')
        cf.cf_login(test_org.name, test_space.name)
        _, cf_service_instances_list = cf_api_get_space_summary(test_space.guid)
        cf_service_instance_guids = [s.guid for s in cf_service_instances_list]
        assert cf_service_instance_guids == list((instance.guid,))

    @priority.medium
    def test_delete_service_instance(self, org_space, instance):
        test_org, test_space = org_space
        step('Login to cf')
        cf.cf_login(test_org.name, test_space.name)
        instance.api_delete()
        _, cf_service_instances_list = cf_api_get_space_summary(test_space.guid)
        assert cf_service_instances_list == []
