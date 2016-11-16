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

from tests.fixtures import assertions
from modules.tap_object_model import ServiceInstance
from modules.markers import priority
from modules.tap_logger import step
from modules.exceptions import UnexpectedResponseError

class TestServicesInOrgs:
    @pytest.mark.skip(reason="DPNG-11178 multiorg not implemented yet")
    @pytest.mark.parametrize("role", ["user"])
    @priority.medium
    def test_cannot_create_instance_as_user_from_different_org(self, context, marketplace_offerings, test_user_clients,
                                                               role):
        client = test_user_clients[role]
        org = "DIFFERENT_ORG"
        errors = []
        for offering in marketplace_offerings:
            offering_id = offering.id
            plan_id = offering.service_plans[0].id
            step("Try to create {} service instance".format(offering.label))
            with pytest.raises(UnexpectedResponseError) as e:
                # TODO org not supported yet
                ServiceInstance.create(context, offering_id=offering_id, plan_id=plan_id, org=org, client=client)
            if e is None or e.value.status != HttpStatus.CODE_FORBIDDEN:
                errors.append("Service '{}' failed to respond with given error status.".format(offering.label))
        assert_no_errors(errors)