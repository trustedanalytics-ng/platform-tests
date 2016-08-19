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

import config
from modules.constants import TapComponent as TAP

default = {
    "api_version": "v1",
    "api_version_alias": "v1.0",
    "health_endpoint": "healthz",
    "get_endpoint": None
}

k8s_core_services = {
    TAP.catalog: {"get_endpoint": "images"},
    TAP.container_broker: {},
    TAP.image_factory: {},
    TAP.template_repository: {"get_endpoint": "templates"},
    TAP.blob_store: {},
    TAP.console_service: {},
    TAP.dashboard: {"health_endpoint": None},
    TAP.message_queue: {"health_endpoint": None}
}

for item in k8s_core_services:
    updated_config = default.copy()
    updated_config.update(k8s_core_services[item])
    k8s_core_services[item] = updated_config

third_party_services = {
    TAP.image_repository: {
        "url": config.ng_image_repository_url,
        "api_version": "v2",
        "api_version_alias": None,
        "health_endpoint": None,
        "get_endpoint": "_catalog"
    }
}