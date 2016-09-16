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

ng_template_example_body = {
    "componentType": "",
    "persistentVolumeClaims": None,
    "deployments": [
        {
            "kind": "Deployment",
            "apiVersion": "extensions/v1beta1",
            "metadata": {
                "name": "$idx_and_short_serviceid",
                "creationTimestamp": None,
                "labels": {
                    "catalog_plan_id": "$catalog_plan_id",
                    "catalog_service_id": "$catalog_service_id",
                    "idx_and_short_serviceid": "$idx_and_short_serviceid",
                    "managed_by": "TAP",
                    "org": "$org",
                    "service_id": "$service_id",
                    "space": "$space"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "idx_and_short_serviceid": "$idx_and_short_serviceid",
                        "service_id": "$service_id"
                    }
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": None,
                        "labels": {
                            "idx_and_short_serviceid": "$idx_and_short_serviceid",
                            "managed_by": "TAP",
                            "service_id": "$service_id"
                        }
                    },
                    "spec": {
                        "volumes": None,
                        "containers": [
                            {
                                "name": "k-ipython",
                                "image": "ipython/scipyserver",
                                "ports": [
                                    {
                                        "containerPort": 8888,
                                        "protocol": "TCP"
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "MANAGED_BY",
                                        "value": "TAP"
                                    },
                                    {
                                        "name": "PASSWORD",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_serviceid-ipython-credentials",
                                                "key": "password"
                                            }
                                        }
                                    }
                                ],
                                "resources": {},
                                "imagePullPolicy": "IfNotPresent"
                            }
                        ],
                        "restartPolicy": "Always",
                        "dnsPolicy": "ClusterFirst",
                        "serviceAccountName": ""
                    }
                },
                "strategy": {}
            },
            "status": {}
        }
    ],
    "services": [
        {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": "$idx_and_short_serviceid",
                "creationTimestamp": None,
                "labels": {
                    "catalog_plan_id": "$catalog_plan_id",
                    "catalog_service_id": "$catalog_service_id",
                    "idx_and_short_serviceid": "$idx_and_short_serviceid",
                    "managed_by": "TAP",
                    "org": "$org",
                    "service_id": "$service_id",
                    "space": "$space"
                }
            },
            "spec": {
                "type": "NodePort",
                "ports": [
                    {
                        "name": "",
                        "protocol": "TCP",
                        "port": 8888,
                        "targetPort": 0,
                        "nodePort": 0
                    }
                ],
                "selector": {
                    "service_id": "$service_id"
                }
            },
            "status": {
                "loadBalancer": {}
            }
        }
    ],
    "serviceAccounts": [
        {
            "kind": "ServiceAccount",
            "apiVersion": "v1",
            "metadata": {
                "name": "$idx_and_short_serviceid",
                "creationTimestamp": None,
                "labels": {
                    "catalog_plan_id": "$catalog_plan_id",
                    "catalog_service_id": "$catalog_service_id",
                    "idx_and_short_serviceid": "$idx_and_short_serviceid",
                    "managed_by": "TAP",
                    "org": "$org",
                    "service_id": "$service_id",
                    "space": "$space"
                }
            },
            "secrets": None
        }
    ],
    "secrets": [
        {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": "$short_serviceid-ipython-credentials",
                "creationTimestamp": None,
                "labels": {
                    "idx_and_short_serviceid": "$idx_and_short_serviceid",
                    "managed_by": "TAP",
                    "service_id": "$service_id"
                }
            },
            "data": {
                "password": "JHJhbmRvbTE="
            }
        }
    ]
}

etcd_template = {
    "body": {
        "componentType": "instance",
        "persistentVolumeClaims": None,
        "deployments": [
            {
                "kind": "Deployment",
                "apiVersion": "extensions\/v1beta1",
                "metadata": {
                    "name": "$idx_and_short_instance_id",
                    "creationTimestamp": None,
                    "labels": {
                        "plan_id": "$plan_id",
                        "offering_id": "$offering_id",
                        "idx_and_short_instance_id": "$idx_and_short_instance_id",
                        "managed_by": "TAP",
                        "org": "$org",
                        "instance_id": "$instance_id",
                        "space": "$space"
                    }
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": {
                            "idx_and_short_instance_id": "$idx_and_short_instance_id",
                            "instance_id": "$instance_id"
                        }
                    },
                    "template": {
                        "metadata": {
                            "creationTimestamp": None,
                            "labels": {
                                "idx_and_short_instance_id": "$idx_and_short_instance_id",
                                "managed_by": "TAP",
                                "instance_id": "$instance_id"
                            }
                        },
                        "spec": {
                            "volumes": None,
                            "containers": [
                                {
                                    "name": "k-etcd",
                                    "image": "127.0.0.1:30000/coreos/etcd:v2.3.6",
                                    "ports": [
                                        {
                                            "containerPort": 4001,
                                            "protocol": "TCP"
                                        },
                                        {
                                            "containerPort": 7001,
                                            "protocol": "TCP"
                                        }
                                    ],
                                    "env": [
                                        {
                                            "name": "MANAGED_BY",
                                            "value": "TAP"
                                        }
                                    ],
                                    "resources": {
                                        "limits": {
                                            "memory": "500M"
                                        },
                                        "requests": {
                                            "memory": "100M"
                                        }
                                    },
                                    "imagePullPolicy": "IfNotPresent"
                                }
                            ],
                            "restartPolicy": "Always",
                            "dnsPolicy": "ClusterFirst",
                            "serviceAccountName": ""
                        }
                    },
                    "strategy": {

                    }
                },
                "status": {

                }
            }
        ],
        "ingresses": None,
        "services": [
            {
                "kind": "Service",
                "apiVersion": "v1",
                "metadata": {
                    "name": "$idx_and_short_instance_id",
                    "creationTimestamp": None,
                    "labels": {
                        "plan_id": "$plan_id",
                        "offering_id": "$offering_id",
                        "idx_and_short_instance_id": "$idx_and_short_instance_id",
                        "managed_by": "TAP",
                        "org": "$org",
                        "instance_id": "$instance_id",
                        "space": "$space"
                    }
                },
                "spec": {
                    "type": "NodePort",
                    "ports": [
                        {
                            "name": "rest",
                            "protocol": "TCP",
                            "port": 4001,
                            "targetPort": 0,
                            "nodePort": 0
                        },
                        {
                            "name": "transport",
                            "protocol": "TCP",
                            "port": 7001,
                            "targetPort": 0,
                            "nodePort": 0
                        }
                    ],
                    "selector": {
                        "instance_id": "$instance_id"
                    }
                },
                "status": {
                    "loadBalancer": {

                    }
                }
            }
        ],
        "serviceAccounts": [
            {
                "kind": "ServiceAccount",
                "apiVersion": "v1",
                "metadata": {
                    "name": "$idx_and_short_instance_id",
                    "creationTimestamp": None,
                    "labels": {
                        "plan_id": "$plan_id",
                        "offering_id": "$offering_id",
                        "idx_and_short_instance_id": "$idx_and_short_instance_id",
                        "managed_by": "TAP",
                        "org": "$org",
                        "instance_id": "$instance_id",
                        "space": "$space"
                    }
                },
                "secrets": None
            }
        ],
        "secrets": None
    },
    "hooks": None
}
