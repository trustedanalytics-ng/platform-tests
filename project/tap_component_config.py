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

TAP_core_services = {name: {} for name in TAP.get_list_internal()}

TAP_core_services.update({
    TAP.catalog: {"get_endpoint": "images"},
    TAP.container_broker: {"get_endpoint": "secret/smtp"},
    TAP.template_repository: {"get_endpoint": "templates"}
})

for item in TAP_core_services:
    updated_config = default.copy()
    updated_config.update(TAP_core_services[item])
    TAP_core_services[item] = updated_config

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
    ServiceLabels.ELASTICSEARCH: [Plan.FREE],
    ServiceLabels.GATEWAY: [Plan.FREE],
    ServiceLabels.GEARPUMP: [Plan.WORKER_1, Plan.WORKER_2, Plan.WORKER_3],
    ServiceLabels.HDFS: [Plan.GET_USER_DIRECTORY, Plan.CREATE_USER_DIRECTORY, Plan.SHARED, Plan.ENCRYPTED,
                         Plan.MULTITENANT],
    ServiceLabels.HIVE: [Plan.MULTITENANT, Plan.SHARED],
    ServiceLabels.INFLUX_DB: [Plan.FREE],
    ServiceLabels.JUPYTER: [Plan.FREE],
    ServiceLabels.KAFKA: [Plan.SHARED],
    ServiceLabels.KERBEROS: [Plan.FREE],
    ServiceLabels.MEMCACHED: [Plan.MEM128MB, Plan.MEM256MB, Plan.MEM512MB],
    ServiceLabels.MONGO_DB: [Plan.FREE, Plan.PERSISTENT, Plan.CLUSTERED],
    ServiceLabels.MOSQUITTO: [Plan.FREE],
    ServiceLabels.MYSQL: [Plan.FREE, Plan.PERSISTENT, Plan.CLUSTERED],
    ServiceLabels.ORIENT_DB: [Plan.FREE, Plan.PERSISTENT],
    ServiceLabels.PSQL94_MULTINODE: [Plan.PERSISTENT],
    ServiceLabels.PSQL: [Plan.FREE, Plan.PERSISTENT, Plan.CLUSTERED],
    ServiceLabels.RABBIT_MQ: [Plan.FREE],
    ServiceLabels.SEAHORSE: [Plan.FREE],
    ServiceLabels.ZOOKEEPER: [Plan.SHARED],
}


offerings_as_parameters = []
for key, val in offerings.items():
    offerings_as_parameters += list(itertools.product([key], val))
