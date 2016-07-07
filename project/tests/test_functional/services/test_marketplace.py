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

import itertools

import pytest

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, ParametrizedService, ServiceLabels, ServicePlan, \
    TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.markers import components, long, priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceType, Space, User
from modules.tap_object_model.flows.services import create_instance_and_key_then_delete_key_and_instance
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_no_errors, assert_raises_http_exception, assert_in_with_retry, \
    assert_unordered_list_equal


logged_components = (TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker,
                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                     TAP.zookeeper_wssb_broker)
pytestmark = [components.service_catalog, components.application_broker, components.gearpump_broker,
              components.hbase_broker, components.kafka_broker, components.smtp_broker,
              components.yarn_broker, components.zookeeper_broker, components.zookeeper_wssb_broker]


class TestMarketplaceServices:

    SERVICES_TESTED_SEPARATELY = [ServiceLabels.YARN, ServiceLabels.HDFS, ServiceLabels.HBASE, ServiceLabels.GEARPUMP,
                                  ServiceLabels.H2O, ServiceLabels.SEAHORSE]

    @staticmethod
    @pytest.fixture(scope="class")
    def marketplace_services(test_space):
        step("Get list of available services from Marketplace")
        return ServiceType.api_get_list_from_marketplace(test_space.guid)

    @classmethod
    @pytest.fixture(scope="class")
    def non_space_developer_users(cls, request, test_org, test_space, class_context):
        step("Create space auditor")
        space_auditor = User.api_create_by_adding_to_space(class_context, test_org.guid, test_space.guid,
                                                           roles=User.SPACE_ROLES["auditor"])
        cls.space_auditor_client = space_auditor.login()
        step("Create space manager client")
        space_manager = User.api_create_by_adding_to_space(class_context, test_org.guid, test_space.guid,
                                                           roles=User.SPACE_ROLES["manager"])
        cls.space_manager_client = space_manager.login()

    def _create_jupyter_instance_and_login(self, param_key, param_value, test_org, test_space):
        param = {param_key: param_value}
        step("Create service instance and check it exist in list")
        jupyter = Jupyter(test_org.guid, test_space.guid, params=param)
        assert_in_with_retry(jupyter.instance, ServiceInstance.api_get_list, test_space.guid)
        step("Get credentials for the new jupyter service instance")
        jupyter.get_credentials()
        jupyter.login()
        terminal = jupyter.connect_to_terminal(terminal_no=0)
        _ = terminal.get_output()
        return terminal

    @priority.medium
    def test_check_marketplace_services_list_vs_cloudfoundry(self, test_space, marketplace_services):
        step("Check that services in cf are the same as in Marketplace")
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace_by_space(test_space.guid)
        assert_unordered_list_equal(marketplace_services, cf_marketplace)

    @long
    @priority.high
    def test_create_and_delete_service_instance_and_keys(self, test_org, test_space, marketplace_services):
        errors = []
        for service_type in marketplace_services:
            if service_type.label in self.SERVICES_TESTED_SEPARATELY:
                continue
            for plan in service_type.service_plans:
                if ParametrizedService.is_parametrized(label=service_type.label, plan_name=plan["name"]):
                    continue
                try:
                    create_instance_and_key_then_delete_key_and_instance(
                        test_org.guid, test_space.guid, service_type.label, plan["guid"], plan["name"])
                except Exception as e:
                    errors.append(e)
        assert_no_errors(errors)

    @priority.low
    def test_create_instance_with_non_required_parameter(self, test_org, test_space):
        param_key = "test_param"
        param_value = "test_value"
        terminal = self._create_jupyter_instance_and_login(param_key, param_value, test_org, test_space)
        terminal.send_input("env\n")
        output = "".join(terminal.get_output())
        assert "{}={}".format(param_key, param_value) in output

    @priority.medium
    def test_cannot_create_service_instance_with_name_of_an_existing_instance(self, test_org, test_space,
                                                                              marketplace_services):
        existing_name = generate_test_object_name()
        step("Create service instance")
        instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.KAFKA,
            name=existing_name,
            service_plan_name=ServicePlan.SHARED
        )
        service_list = ServiceInstance.api_get_list(space_guid=test_space.guid)
        step("Check that the instance was created")
        assert instance in service_list, "Instance was not created"
        errors = []
        for service_type in marketplace_services:
            plan_guid = next(iter(service_type.service_plan_guids))
            step("Try to create {} service instance".format(service_type.label))
            with pytest.raises(UnexpectedResponseError) as e:
                ServiceInstance.api_create(test_org.guid, test_space.guid, service_type.label,
                                           existing_name, service_plan_guid=plan_guid)
            if e is None or e.value.status != HttpStatus.CODE_CONFLICT:
                errors.append("Service '{}' failed to respond with given error status.".format(service_type.label))
        assert_no_errors(errors)
        assert_unordered_list_equal(service_list, ServiceInstance.api_get_list(space_guid=test_space.guid),
                                    "Some new services were created")

    @priority.low
    @pytest.mark.bugs("DPNG-5154 Http status 500 when trying to create a service instance without a name")
    def test_cannot_create_instance_without_a_name(self, test_org, test_space):
        expected_instance_list = ServiceInstance.api_get_list(test_space.guid)
        step("Check that instance cannot be created with empty name")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ServiceInstance.api_create_with_plan_name, test_org.guid,
                                     test_space.guid, ServiceLabels.KAFKA, "",
                                     service_plan_name=ServicePlan.SHARED)
        assert_unordered_list_equal(expected_instance_list, ServiceInstance.api_get_list(test_space.guid),
                                    "New instance was created")

    @priority.medium
    @pytest.mark.usefixtures("non_space_developer_users")
    def test_cannot_create_instance_as_non_space_developer(self, test_org, test_space, marketplace_services):
        test_clients = {"space_auditor": self.space_auditor_client, "space_manager": self.space_manager_client}
        errors = []
        for service_type, (name, client) in itertools.product(marketplace_services, test_clients.items()):
            for plan in service_type.service_plans:
                with pytest.raises(UnexpectedResponseError) as e:
                    ServiceInstance.api_create(test_org.guid, test_space.guid, service_type.label,
                                               service_plan_guid=plan["guid"], client=client)
                if e is None or e.value.status != HttpStatus.CODE_FORBIDDEN:
                    errors.append("Service '{}' failed to respond with given error status.".format(service_type.label))
        assert_no_errors(errors)

    @priority.low
    @pytest.mark.bugs("DPNG-6086 Adding service key to H2O instance fails")
    def test_create_h2o_service_instance_and_keys(self, test_org, test_space, marketplace_services):
        label = ServiceLabels.H2O
        h2o = next((s for s in marketplace_services if s.label == label), None)
        if h2o is None:
            pytest.skip("h2o is not available in Marketplace")
        errors = []
        for plan in h2o.service_plans:
            try:
                create_instance_and_key_then_delete_key_and_instance(
                    test_org.guid, test_space.guid, label, plan["guid"], plan["name"])
            except Exception as e:
                errors.append(e)
        assert_no_errors(errors)

    @priority.low
    @pytest.mark.bugs("DPNG-3474 Command cf create-service-key does not work for yarn broker")
    def test_create_yarn_service_instance_and_keys(self, test_org, test_space, marketplace_services):
        label = ServiceLabels.YARN
        yarn = next(s for s in marketplace_services if s.label == label)
        errors = []
        for plan in yarn.service_plans:
            try:
                create_instance_and_key_then_delete_key_and_instance(
                    test_org.guid, test_space.guid, label, plan["guid"], plan["name"])
            except Exception as e:
                errors.append(e)
        assert_no_errors(errors)

    @priority.low
    @pytest.mark.bugs("DPNG-2798 Enable HBase broker to use Service Keys")
    def test_create_hbase_service_instance_and_keys(self, test_org, test_space, marketplace_services):
        label = ServiceLabels.HBASE
        hbase = next(s for s in marketplace_services if s.label == label)
        errors = []
        for plan in hbase.service_plans:
            try:
                create_instance_and_key_then_delete_key_and_instance(
                    test_org.guid, test_space.guid, label, plan["guid"], plan["name"])
            except Exception as e:
                errors.append(e)
        assert_no_errors(errors)

    @priority.low
    @pytest.mark.bugs("DPNG-6087 Connection to service catalog timedout - cannot create gearpump instance")
    def test_create_gearpump_service_instance_and_keys(self, test_org, test_space, marketplace_services):
        label = ServiceLabels.GEARPUMP
        gearpump = next(s for s in marketplace_services if s.label == label)
        errors = []
        for plan in gearpump.service_plans:
            try:
                create_instance_and_key_then_delete_key_and_instance(
                    test_org.guid, test_space.guid, label, plan["guid"], plan["name"])
            except Exception as e:
                errors.append(e)
        assert_no_errors(errors)

    @priority.low
    def test_get_service_instance_summary_from_empty_space(self, test_org, test_space, marketplace_services):
        step("Create a service instance in one space")
        service_type = next(s for s in marketplace_services if s.label == ServiceLabels.KAFKA)
        ServiceInstance.api_create(org_guid=test_org.guid, space_guid=test_space.guid,
                                   service_label=service_type.label,
                                   service_plan_guid=service_type.service_plan_guids[0])
        test_space = Space.api_create(test_org)
        step("Get service instance summary in another space")
        summary = ServiceInstance.api_get_keys(test_space.guid)
        step("Check that service instance summary is empty in the second space")
        assert summary == {}
