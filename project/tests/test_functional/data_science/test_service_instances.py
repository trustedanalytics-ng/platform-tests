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

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import ServiceLabels, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance

logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.service_exposer)]


class TestDataScienceInstances(object):

    @priority.high
    @pytest.mark.parametrize("service_label", [ServiceLabels.JUPYTER, ServiceLabels.H2O])
    def test_create_and_delete_service_instances(self, context, service_label, marketplace_offerings):
        service_type = next((s for s in marketplace_offerings if s.label == service_label), None)
        assert service_type is not None, "{} service is not available in Marketplace".format(service_label)
        plan = next(iter(service_type.service_plans))
        step("Create service instance")
        instance = ServiceInstance.create_with_name(
            context=context,
            offering_label=service_type.label,
            plan_name=plan.name
        )
        instance.ensure_running()
        validator = ApplicationStackValidator(instance)
        validator.validate(validate_application=False)
        step("Stop service instance")
        instance.stop()
        instance.ensure_stopped()
        step("Delete service instance")
        instance.delete()
        instance.ensure_deleted()


