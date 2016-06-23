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

from configuration import config
from modules.constants import TapComponent as TAP
from modules.http_calls import kubernetes_broker as k8s_broker_client
from modules.markers import components, priority
from modules.tap_logger import step


logged_components = (TAP.kubernetes_broker,)
pytestmark = [components.kubernetes_broker, priority.low]


@pytest.mark.skipif(not config.CONFIG["kubernetes"], reason="No point to run without kuberentes")
class TestKubernetesCatalog:
    KUBERNETES_TAG = "k8s"

    def test_all_services_have_k8s_tag(self):
        step("Get catalog.")
        catalog = k8s_broker_client.k8s_broker_get_catalog()

        step("Check that all services have tags.")
        services_without_tags = []
        for service in catalog["services"]:
            if self.KUBERNETES_TAG not in service["tags"]:
                services_without_tags.append(service["name"])

        assert len(services_without_tags) == 0, "Services without {} tag: {}".format(self.KUBERNETES_TAG,
                                                                                     ",".join(services_without_tags))
