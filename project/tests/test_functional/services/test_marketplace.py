#
# Copyright (c) 2015-2016 Intel Corporation
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

from modules.constants import PARAMETRIZED_SERVICE_INSTANCES, ServiceCatalogHttpStatus as HttpStatus, ServiceLabels,\
    TapComponent as TAP
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, long, priority
from modules.service_tools.ipython import iPython
from modules.tap_object_model import ServiceInstance, ServiceKey, ServiceType, Space, User
from modules.test_names import get_test_name
from tests.fixtures.test_data import TestData


logged_components = (TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker,
                     TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                     TAP.zookeeper_wssb_broker)
pytestmark = [components.service_catalog, components.application_broker, components.gearpump_broker,
              components.hbase_broker, components.hdfs_broker, components.kafka_broker, components.smtp_broker,
              components.yarn_broker, components.zookeeper_broker, components.zookeeper_wssb_broker]


class MarketplaceServices(TapTestCase):

    SERVICES_TESTED_SEPARATELY = [ServiceLabels.YARN, ServiceLabels.HDFS, ServiceLabels.HBASE, ServiceLabels.GEARPUMP,
                                  ServiceLabels.H2O]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def marketplace_services(cls, test_org, test_space):
        cls.step("Get list of available services from Marketplace")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)

    @classmethod
    @pytest.fixture(scope="class")
    def non_space_developer_users(cls, test_org, test_space):
        cls.step("Create space auditor client")
        cls.space_auditor_client = User.api_create_by_adding_to_space(test_org.guid, test_space.guid,
                                                                      roles=User.SPACE_ROLES["auditor"]).login()
        cls.step("Create space manager client")
        cls.space_manager_client = User.api_create_by_adding_to_space(test_org.guid, test_space.guid,
                                                                      roles=User.SPACE_ROLES["manager"]).login()

    def _create_and_delete_service_instance_and_keys(self, org_guid, space_guid, service_label, plan_guid):
        self.step("Create service instance")
        instance = ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label=service_label,
            service_plan_guid=plan_guid
        )
        self.step("Check that the instance was created")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        self.assertIn(instance, instances)
        service_key_exception = None
        try:
            self.step("Check that the instance exists in summary and has no service keys")
            summary = ServiceInstance.api_get_keys(space_guid)
            self.assertIn(instance, summary)
            self.assertEqual(summary[instance], [])  # there are no keys for this instance
            self.step("Create a key for the instance and check it's correctness")
            instance_key = ServiceKey.api_create(instance.guid)
            summary = ServiceInstance.api_get_keys(space_guid)
            self.assertEqual(summary[instance][0], instance_key)
            self.step("Delete key and check that it's deleted")
            instance_key.api_delete()
            summary = ServiceInstance.api_get_keys(space_guid)
            self.assertEqual(summary[instance], [])
        except AssertionError as e:
            service_key_exception = e
        try:
            self.step("Delete the instance")
            instance.api_delete()
            self.step("Check that the instance was deleted")
            instances = ServiceInstance.api_get_list(space_guid=space_guid)
            self.assertNotIn(instance, instances)
        except AssertionError as e:
            if service_key_exception is not None:
                raise service_key_exception
            raise e
        if service_key_exception is not None:
            raise service_key_exception

    def _create_ipython_instance_and_login(self, param_key, param_value):
        param = {param_key: param_value}
        self.step("Create service instance and check it exist in list")
        ipython = iPython(self.test_org.guid, self.test_space.guid, params=param)
        self.assertInWithRetry(ipython.instance, ServiceInstance.api_get_list, self.test_space.guid)
        self.step("Get credentials for the new ipython service instance")
        ipython.get_credentials()
        ipython.login()
        terminal = ipython.connect_to_terminal(terminal_no=0)
        _ = terminal.get_output()
        return terminal

    @priority.medium
    def test_check_marketplace_services_list_vs_cloudfoundry(self):
        self.step("Check that services in cf are the same as in Marketplace")
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace_by_space(TestData.test_space.guid)
        self.assertUnorderedListEqual(self.marketplace, cf_marketplace)

    @long
    @priority.high
    def test_create_and_delete_service_instance_and_keys(self):
        tested_service_types = [st for st in self.marketplace if st.label not in PARAMETRIZED_SERVICE_INSTANCES +
                                self.SERVICES_TESTED_SEPARATELY]
        for service_type in tested_service_types:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self._create_and_delete_service_instance_and_keys(TestData.test_org.guid, TestData.test_space.guid,
                                                                      service_type.label, plan["guid"])

    @priority.low
    def test_create_instance_with_non_required_parameter(self):
        param_key = "test_param"
        param_value = "test_value"
        terminal = self._create_ipython_instance_and_login(param_key, param_value)
        terminal.send_input("env\n")
        output = "".join(terminal.get_output())
        self.assertIn("{}={}".format(param_key, param_value), output)

    @priority.medium
    def test_cannot_create_service_instance_with_name_of_an_existing_instance(self):
        existing_name = get_test_name()
        self.step("Create service instance")
        instance = ServiceInstance.api_create(
            org_guid=TestData.test_org.guid,
            space_guid=TestData.test_space.guid,
            service_label=ServiceLabels.KAFKA,
            name=existing_name,
            service_plan_name="shared"
        )
        service_list = ServiceInstance.api_get_list(space_guid=TestData.test_space.guid)
        self.step("Check that the instance was created")
        self.assertIn(instance, service_list, "Instance was not created")
        for service_type in self.marketplace:
            plan_guid = next(iter(service_type.service_plan_guids))
            with self.subTest(service_type=service_type):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT,
                                                    HttpStatus.MSG_SERVICE_NAME_TAKEN.format(existing_name),
                                                    ServiceInstance.api_create, TestData.test_org.guid,
                                                    TestData.test_space.guid, service_type.label, existing_name,
                                                    service_plan_guid=plan_guid)
        self.assertUnorderedListEqual(service_list, ServiceInstance.api_get_list(space_guid=TestData.test_space.guid),
                                      "Some new services were created")

    @priority.low
    @pytest.mark.bugs("DPNG-5154 Http status 500 when trying to create a service instance without a name")
    def test_cannot_create_instance_without_a_name(self):
        expected_instance_list = ServiceInstance.api_get_list(TestData.test_space.guid)
        self.step("Check that instance cannot be created with empty name")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            ServiceInstance.api_create, TestData.test_org.guid, TestData.test_space.guid,
                                            ServiceLabels.KAFKA, "", service_plan_name="shared")
        self.assertUnorderedListEqual(expected_instance_list, ServiceInstance.api_get_list(TestData.test_space.guid),
                                      "New instance was created")

    @priority.medium
    @pytest.mark.usefixtures("non_space_developer_users")
    def test_cannot_create_instance_as_non_space_developer(self):
        test_clients = {"space_auditor": self.space_auditor_client, "space_manager": self.space_manager_client}
        for service_type, (name, client) in itertools.product(self.marketplace, test_clients.items()):
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self.step("Try to create new instance")
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        ServiceInstance.api_create, TestData.test_org.guid,
                                                        TestData.test_space.guid, service_type.label,
                                                        service_plan_guid=plan["guid"], client=client)

    @priority.low
    @pytest.mark.bugs("DPNG-6086 Adding service key to H2O instance fails")
    def test_create_h2o_service_instance_and_keys(self):
        label = ServiceLabels.H2O
        h2o = next((s for s in self.marketplace if s.label == label), None)
        if h2o is None:
            self.skipTest("h2o is not available in Marketplace")
        for plan in h2o.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance_and_keys(TestData.test_org.guid, TestData.test_space.guid,
                                                                  label, plan["guid"])

    @priority.low
    @pytest.mark.bugs("DPNG-3474 Command cf create-service-key does not work for yarn broker")
    def test_create_yarn_service_instance_and_keys(self):
        label = ServiceLabels.YARN
        yarn = next(s for s in self.marketplace if s.label == label)
        for plan in yarn.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance_and_keys(TestData.test_org.guid, TestData.test_space.guid,
                                                                  label, plan["guid"])

    @priority.low
    def test_create_hdfs_service_instance_and_keys(self):
        """DPNG-3273 Enable HDFS broker to use Service Keys"""
        label = ServiceLabels.HDFS
        hdfs = next(s for s in self.marketplace if s.label == label)
        for plan in hdfs.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance_and_keys(TestData.test_org.guid, TestData.test_space.guid,
                                                                  label, plan["guid"])

    @priority.low
    @pytest.mark.bugs("DPNG-2798 Enable HBase broker to use Service Keys")
    def test_create_hbase_service_instance_and_keys(self):
        label = ServiceLabels.HBASE
        hbase = next(s for s in self.marketplace if s.label == label)
        for plan in hbase.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance_and_keys(TestData.test_org.guid, TestData.test_space.guid,
                                                                  label, plan["guid"])

    @priority.low
    @pytest.mark.bugs("DPNG-6087 Connection to service catalog timedout - cannot create gearpump instance")
    def test_create_gearpump_service_instance_and_keys(self):
        label = ServiceLabels.GEARPUMP
        gearpump = next(s for s in self.marketplace if s.label == label)
        for plan in gearpump.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance_and_keys(TestData.test_org.guid, TestData.test_space.guid,
                                                                  label, plan["guid"])

    @priority.low
    def test_get_service_instance_summary_from_empty_space(self):
        self.step("Create a service instance in one space")
        service_type = next(s for s in self.marketplace if s.label == ServiceLabels.KAFKA)
        ServiceInstance.api_create(org_guid=TestData.test_org.guid, space_guid=TestData.test_space.guid,
                                   service_label=service_type.label,
                                   service_plan_guid=service_type.service_plan_guids[0])
        test_space = Space.api_create(TestData.test_org)
        self.step("Get service instance summary in another space")
        summary = ServiceInstance.api_get_keys(test_space.guid)
        self.step("Check that service instance summary is empty in the second space")
        self.assertEqual(summary, {})
