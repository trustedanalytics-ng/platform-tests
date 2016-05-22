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

import config
from modules.constants import HttpStatus, TapComponent as TAP
from modules.markers import priority, components
from modules.http_calls import kubernetes_broker
from modules.runner.tap_test_case import TapTestCase
from modules.tap_logger import step
from modules import test_names


logged_components = (TAP.kubernetes_broker,)
pytestmark = [priority.low, components.kubernetes_broker]


@pytest.mark.skipif(not config.kubernetes, reason="No point to run without kubernetes")
class TestKubernetesDeleteService(TapTestCase):

    def test_delete_not_existing_dynamic_service(self):
        step("Try to delete not existing dynamic service")
        invalid_service_name = test_names.generate_test_object_name(short=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_GONE, "",
                                            kubernetes_broker.k8s_broker_delete_service,
                                            service_name=invalid_service_name)

    def test_delete_dynamic_service_without_name(self):
        step("Try to delete dynamic service without name")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_GONE, "",
                                            kubernetes_broker.k8s_broker_delete_service,
                                            service_name=None)
