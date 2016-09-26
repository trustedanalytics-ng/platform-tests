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
from modules.constants import ServiceLabels, ServicePlan as Plan, TapComponent as TAP

default = {
    "api_version": "v1",
    "api_version_alias": "v1.0",
    "health_endpoint": "healthz",
    "get_endpoint": None
}

api_service = {
    TAP.api_service: {
        "get_endpoint": "catalog",
        "api_version": "v1",
        "api_version_alias": None
    }
}

k8s_core_services = {
    TAP.catalog: {"get_endpoint": "images"},
    TAP.container_broker: {"get_endpoint": "secret/smtp"},
    TAP.image_factory: {},
    TAP.template_repository: {"get_endpoint": "templates"},
    TAP.blob_store: {}
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
    },

    TAP.message_queue: {
        "health_endpoint": None,
        "get_endpoint": None
    }
}

offerings = {
    ServiceLabels.CASSANDRA21: [Plan.FREE],
    ServiceLabels.CONSUL: [Plan.FREE],
    ServiceLabels.COUCH_DB: [Plan.FREE],
    ServiceLabels.ETCD: [Plan.FREE],
    ServiceLabels.INFLUX_DB: [Plan.FREE],
    ServiceLabels.JUPYTER: [Plan.FREE],
    ServiceLabels.LOGSTASH: [Plan.FREE],
    ServiceLabels.MEMCACHED: [Plan.MEM128MB],
    ServiceLabels.MOSQUITTO: [Plan.FREE],
    ServiceLabels.PSQL: [Plan.FREE],
    ServiceLabels.RABBIT_MQ: [Plan.FREE],
    ServiceLabels.REDIS: [Plan.FREE],
    ServiceLabels.GATEWAY: [Plan.FREE],
}
