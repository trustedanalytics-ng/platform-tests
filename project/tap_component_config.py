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


class PlanKeys:
    NODES = "nodes"
    MEMORY = "memory"
    STORAGE = "storage"
    WORKERS = "workers"
    WORKER_MEMORY = "worker-memory"
    SMOKE_TESTS = "smoke_tests"

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
    TAP.template_repository: {"get_endpoint": "templates"},
    TAP.uploader: {"health_endpoint": "health"},
    TAP.downloader: {"health_endpoint": "health"},
    TAP.das: {"health_endpoint": "health"},
    TAP.dataset_publisher: {"health_endpoint": "health"},
    TAP.workflow_scheduler: {"health_endpoint": "health"},
    TAP.platform_snapshot: {"health_endpoint": "health"},
    TAP.data_catalog: {"health_endpoint": "health"},
    TAP.metadata_parser: {"health_endpoint": "health"},
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
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "1Gi",
            PlanKeys.STORAGE: "5.0G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "4Gi",
            PlanKeys.STORAGE: "50G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.ELASTICSEARCH24: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.STORAGE: "20G",
            PlanKeys.SMOKE_TESTS: False,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "12Gi",
            PlanKeys.STORAGE: "200G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.GATEWAY: {
        Plan.SINGLE: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "128Mi",
            PlanKeys.STORAGE: None,
            PlanKeys.SMOKE_TESTS: True,
        }
    },
    ServiceLabels.GEARPUMP: {
        Plan.SMALL: {
            PlanKeys.WORKERS: 1,
            PlanKeys.WORKER_MEMORY: "512Mi",
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.SMOKE_TESTS: False,
        }, Plan.MEDIUM: {
            PlanKeys.WORKERS: 3,
            PlanKeys.WORKER_MEMORY: "512Mi",
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.HDFS: {
        Plan.PLAIN_DIR: {
            PlanKeys.SMOKE_TESTS: False,
        }, 
        Plan.ENCRYPTED_DIR: {
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.HIVE: {
        Plan.STANDARD: {
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.H2O: {
        Plan.SINGLE: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "512Mi",
            PlanKeys.STORAGE: None,
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.INFLUX_DB_110: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.STORAGE: "10G",
            PlanKeys.SMOKE_TESTS: True,
        }
    },
    ServiceLabels.JUPYTER: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.STORAGE: "1.0G",
            PlanKeys.SMOKE_TESTS: False,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "8Gi",
            PlanKeys.STORAGE: "1.0G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.KAFKA: {
        Plan.SHARED: {
            PlanKeys.SMOKE_TESTS: True,
        }
    },
    ServiceLabels.KERBEROS: {
        Plan.SHARED: {
            PlanKeys.SMOKE_TESTS: True,
        }
    },
    ServiceLabels.MONGO_DB_30: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "1Gi",
            PlanKeys.STORAGE: "10G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "8Gi",
            PlanKeys.STORAGE: "100G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.MOSQUITTO: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "512M",
            PlanKeys.STORAGE: "5.0G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "4Gi",
            PlanKeys.STORAGE: "20G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.MYSQL: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "1Gi",
            PlanKeys.STORAGE: "10G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "6Gi",
            PlanKeys.STORAGE: "100G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.NEO4J: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.STORAGE: "10G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "6Gi",
            PlanKeys.STORAGE: "100G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.ORIENT_DB: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.STORAGE: "20G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "6Gi",
            PlanKeys.STORAGE: "100G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.PSQL: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "1Gi",
            PlanKeys.STORAGE: "10G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "4Gi",
            PlanKeys.STORAGE: "50G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.RABBIT_MQ: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "512M",
            PlanKeys.STORAGE: "2.0G",
            PlanKeys.SMOKE_TESTS: True,
        }, 
        Plan.SINGLE_MEDIUM: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "2Gi",
            PlanKeys.STORAGE: "10G",
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.REDIS: {
        Plan.SINGLE_SMALL: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "512M",
            PlanKeys.STORAGE: "5.0G",
            PlanKeys.SMOKE_TESTS: True,
        }
    },
    ServiceLabels.SCORING_ENGINE: {
        Plan.SIMPLE: {
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.SCORING_PIPELINES: {
        Plan.SINGLE: {
            PlanKeys.NODES: 1,
            PlanKeys.MEMORY: "500M",
            PlanKeys.STORAGE: None,
            PlanKeys.SMOKE_TESTS: False,
        }
    },
    ServiceLabels.ZOOKEEPER: {
        Plan.STANDARD: {
            PlanKeys.SMOKE_TESTS: False,
        }
    },
}

SERVICES_TESTED_SEPARATELY = [ServiceLabels.HDFS, ServiceLabels.SEAHORSE, ServiceLabels.H2O]

offerings_as_parameters = []
filtered_offerings = []
for key, val in offerings.items():
    offerings_as_parameters += list(itertools.product([key], val.keys()))
    if key not in SERVICES_TESTED_SEPARATELY:
        filtered_offerings += list(itertools.product([key], val.keys()))