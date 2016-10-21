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

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, ApiServiceHttpStatus, ServiceLabels, ServicePlan, \
    TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.markers import long, priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceOffering
from modules.test_names import generate_test_object_name
from tests.fixtures import assertions
from tests.fixtures.assertions import assert_no_errors, assert_raises_http_exception, assert_in_with_retry, \
    assert_unordered_list_equal


logged_components = (TAP.service_catalog, TAP.gearpump_broker, TAP.hbase_broker,
                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                     TAP.zookeeper_wssb_broker)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.gearpump_broker, TAP.hbase_broker,
                                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                                     TAP.zookeeper_wssb_broker)]


class TestMarketplaceServices:
    SERVICES_TESTED_SEPARATELY = [ServiceLabels.HDFS, ServiceLabels.SEAHORSE]

    def _create_jupyter_instance_and_login(self, context, param_key, param_value):
        param = {param_key: param_value}
        step("Create service instance and check it exist in list")
        jupyter = Jupyter(context, params=param)
        assert_in_with_retry(jupyter.instance, ServiceInstance.get_list)
        step("Get credentials for the new jupyter service instance")
        jupyter.get_credentials()
        jupyter.login()
        terminal = jupyter.connect_to_terminal(terminal_no=0)
        _ = terminal.get_output()
        return terminal

    @long
    @priority.high
    @pytest.mark.parametrize("role", ["user"])
    def test_create_and_delete_service_instance(self, context, non_parametrized_marketplace_services,
                                                test_user_clients, role):
        client = test_user_clients[role]
        offering, plan = non_parametrized_marketplace_services
        self._skip_if_service_excluded(offering)

        step("Create an instance")
        instance = ServiceInstance.create(context, offering_id=offering.id,  plan_id=plan.id, client=client)
        step("Ensure that instance is running")
        instance.ensure_running()
        step("Check that service instance is present")
        assert_in_with_retry(instance, ServiceInstance.get_list, name=instance.name)
        step("Delete an instance")
        instance.delete()
        assertions.assert_not_in_by_id_with_retry(instance.id, ServiceInstance.get_list)

    def _skip_if_service_excluded(self, offering):
        if offering.label in self.SERVICES_TESTED_SEPARATELY:
            pytest.skip(msg="Offering {} is tested separately".format(offering.label))

    @pytest.mark.skip(reason="DPNG-10885 credentials endpoint is not implemented yet")
    @priority.low
    def test_create_instance_with_non_required_parameter_and_check_credentials(self, context):
        param_key = "test_param"
        param_value = "test_value"
        step("Create service instance with additional params")
        terminal = self._create_jupyter_instance_and_login(context, param_key, param_value)
        terminal.send_input("env\n")
        output = "".join(terminal.get_output())
        step("Verify if additionals params are returned in credentials")
        assert "{}={}".format(param_key, param_value) in output

    @priority.medium
    def test_cannot_create_service_instance_with_name_of_an_existing_instance(self, context, marketplace_offerings):
        existing_name = generate_test_object_name(short=True)
        step("Create service instance")
        instance = ServiceInstance.create_with_name(
            context=context,
            offering_label=ServiceLabels.RABBIT_MQ,
            name=existing_name,
            plan_name=ServicePlan.FREE
        )
        step("Ensure that instance is running")
        instance.ensure_running()
        step("Check that the instance was created")
        instances = ServiceInstance.get_list()
        assert instance in instances, "Instance was not created"
        errors = []
        for offering in marketplace_offerings:
            offering_id = offering.id
            plan_id = offering.service_plans[0].id
            step("Try to create {} service instance".format(offering.label))
            with pytest.raises(UnexpectedResponseError) as e:
                ServiceInstance.create(context, offering_id=offering_id,  plan_id=plan_id, name=existing_name)
            if e is None or e.value.status != HttpStatus.CODE_CONFLICT:
                errors.append("Service '{}' failed to respond with given error status.".format(offering.label))
        assert_no_errors(errors)
        assert_unordered_list_equal(instances, ServiceInstance.get_list(), "Some new services were created")

    @priority.low
    def test_cannot_create_instance_without_a_name(self, context):
        expected_instance_list = ServiceInstance.get_list()
        step("Check that instance cannot be created with empty name")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, ApiServiceHttpStatus.MSG_BAD_REQUEST,
                                     ServiceInstance.create_with_name, context=context,
                                     offering_label=ServiceLabels.RABBIT_MQ, plan_name=ServicePlan.FREE, name="")
        assert_unordered_list_equal(expected_instance_list, ServiceInstance.get_list(), "New instance was created")

