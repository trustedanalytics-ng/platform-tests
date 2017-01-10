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

from modules.constants import ServiceLabels, ServicePlan as Plan, TapComponent as TAP

default = {
    "api_version": "v1",
    "api_version_alias": "v1.0",
    "health_endpoint": "healthz",
    "get_endpoint": None
}

api_service = {
    TAP.api_service: {
        "get_endpoint": "offerings",
        "api_version": "v3",
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
        "url": None,
        "kubernetes_service_name": "docker-registry",
        "kubernetes_namespace": "kube-system",
        "api_version": "v2",
        "api_version_alias": None,
        "health_endpoint": None,
        "get_endpoint": "_catalog",
    },

    TAP.message_queue: {
        "health_endpoint": None,
        "get_endpoint": None
    }
}

offerings = {
    ServiceLabels.COUCH_DB: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "1Gi",
            "storage": "5.0G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "4Gi",
            "storage": "50G"
        }
    },
    ServiceLabels.ELASTICSEARCH17: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "2Gi",
            "storage": "20G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "12Gi",
            "storage": "200G"
        }
    },
    ServiceLabels.GATEWAY: {
        Plan.SINGLE: {
            "nodes": 1,
            "memory": "128Mi",
            "storage": None
        }
    },
    ServiceLabels.GEARPUMP: {
        Plan.SMALL: {
            "workers": 1,
            "worker-memory": "512Mi",
            "memory": "2Gi"
        }, Plan.MEDIUM: {
            "workers": 3,
            "worker-memory": "512Mi",
            "memory": "2Gi"
        }
    },
    ServiceLabels.HBASE: {
        Plan.ORG_SHARED: None
    },
    ServiceLabels.HDFS: {
        Plan.PLAIN_DIR: None, 
        Plan.ENCRYPTED_DIR: None
    },
    ServiceLabels.HIVE: {
        Plan.STANDARD: None
    },
    ServiceLabels.H2O: {
        Plan.SINGLE: {
            "nodes": 1,
            "memory": "512Mi",
            "storage": None
        }
    },
    ServiceLabels.INFLUX_DB_110: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "2Gi",
            "storage": "10G"
        }
    },
    ServiceLabels.JUPYTER: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "2Gi",
            "storage": "1.0G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "8Gi",
            "storage": "1.0G"
        }
    },
    ServiceLabels.KAFKA: {
        Plan.SHARED: None
    },
    ServiceLabels.KERBEROS: {
        Plan.SHARED: None
    },
    ServiceLabels.MONGO_DB_30: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "1Gi",
            "storage": "10G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "8Gi",
            "storage": "100G"
        }
    },
    ServiceLabels.MOSQUITTO: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "512Mi",
            "storage": "5.0G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "4Gi",
            "storage": "20G"
        }
    },
    ServiceLabels.MYSQL: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "1Gi",
            "storage": "10G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "6Gi",
            "storage": "100G"
        }
    },
    ServiceLabels.NEO4J: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "2Gi",
            "storage": "10G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "6Gi",
            "storage": "100G"
        }
    },
    ServiceLabels.ORIENT_DB: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "2Gi",
            "storage": "20G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "6Gi",
            "storage": "100G"
        }
    },
    ServiceLabels.PSQL: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "1Gi",
            "storage": "10G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "6Gi",
            "storage": "100G"
        }
    },
    ServiceLabels.RABBIT_MQ: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "512Mi",
            "storage": "2.0G"
        }, 
        Plan.SINGLE_MEDIUM: {
            "nodes": 1,
            "memory": "2Gi",
            "storage": "10G"
        }
    },
    ServiceLabels.REDIS: {
        Plan.SINGLE_SMALL: {
            "nodes": 1,
            "memory": "512Mi",
            "storage": "5.0G"
        }
    },
    ServiceLabels.SCORING_ENGINE: {
        Plan.SIMPLE: None
    },
    ServiceLabels.SCORING_PIPELINES: {
        Plan.SINGLE: {
            "nodes": 1,
            "memory": "500M",
            "storage": None
        }
    },
    ServiceLabels.ZOOKEEPER: {
        Plan.STANDARD: None
    },
}


offerings_as_parameters = []
for key, val in offerings.items():
    offerings_as_parameters += list(itertools.product([key], val.keys()))
