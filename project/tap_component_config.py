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
        "api_version": "v2",
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
    ServiceLabels.COUCH_DB: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.ELASTICSEARCH17: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.GATEWAY: [Plan.SINGLE],
    ServiceLabels.GEARPUMP: [Plan.SMALL, Plan.MEDIUM],
    ServiceLabels.HBASE: [Plan.ORG_SHARED],
    ServiceLabels.HDFS: [Plan.PLAN_DIR, Plan.ENCRYPTED_DIR],
    ServiceLabels.HIVE: [Plan.STANDARD],
    ServiceLabels.H2O: [Plan.SINGLE],
    ServiceLabels.INFLUX_DB: [Plan.SINGLE_SMALL],
    ServiceLabels.JUPYTER: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.KAFKA: [Plan.SHARED],
    ServiceLabels.KERBEROS: [Plan.SHARED],
    ServiceLabels.MONGO_DB_26: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.MONGO_DB_30: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.MOSQUITTO: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.MYSQL: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.NEO4J: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.ORIENT_DB: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.PSQL: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.RABBIT_MQ: [Plan.SINGLE_SMALL, Plan.SINGLE_MEDIUM],
    ServiceLabels.REDIS: [Plan.SINGLE_SMALL],
    ServiceLabels.SCORING_ENGINE: [Plan.SIMPLE],
    ServiceLabels.SCORING_PIPELINES: [Plan.SIMPLE],
    ServiceLabels.ZOOKEEPER: [Plan.STANDARD],
}


offerings_as_parameters = []
for key, val in offerings.items():
    offerings_as_parameters += list(itertools.product([key], val))
