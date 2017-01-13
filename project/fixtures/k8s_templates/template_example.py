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


example_template_body = [{
    "componentType": "instance",
    "persistentVolumeClaims": None,
    "deployments": [
        {
            "kind": "Deployment",
            "apiVersion": "extensions/v1beta1",
            "metadata": {
                "name": "$short_instance_id",
                "creationTimestamp": None,
                "labels":
                    {
                        "instance_id": "$instance_id",
                        "managed_by": "TAP",
                        "org": "$org",
                        "short_instance_id": "$short_instance_id",
                        "space": "$space"
                    }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "instance_id": "$instance_id",
                        "managed_by": "TAP",
                        "short_instance_id": "$short_instance_id"
                    }
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": None,
                        "labels": {
                            "instance_id": "$instance_id",
                            "managed_by": "TAP",
                            "short_instance_id": "$short_instance_id"
                        }
                    },
                    "spec": {
                        "volumes": None,
                        "containers": [
                            {
                                "name": "tapng-gateway",
                                "image": "$repository_uri/tapng-gateway",
                                "ports": [
                                    {
                                        "containerPort": 8080,
                                        "protocol": "TCP"
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "GATEWAY_ID",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "id"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_INDEX",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "index"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_TRACE",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "trace"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_ROOT",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.root"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_HOST",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.host"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_PORT",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.port"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_TOKEN",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.token"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_AUTHMETHOD",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.authmethod"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_DEVICEKEYSURI",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.devicekeysuri"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_SERVER_TOLERABLEJWTAGE",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "server.tolerablejwtage"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_PUB_URI",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "pub.uri"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_PUB_TOPIC",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "pub.topic"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_PUB_ACK",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "pub.ack"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_PUB_COMPRESS",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "pub.compress"
                                            }
                                        }
                                    },
                                    {
                                        "name": "GATEWAY_PUB_FLUSHFREQ",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "Name": "$short_instance_id-gateway-args",
                                                "key": "pub.flushfreq"
                                            }
                                        }
                                    },
                                    {
                                        "name": "MANAGED_BY",
                                        "value": "TAP"
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
    "ingresses": None,
    "services": [
        {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": "$short_instance_id",
                "creationTimestamp": None,
                "labels": {
                    "instance_id": "$instance_id",
                    "managed_by": "TAP",
                    "org": "$org",
                    "short_instance_id": "$short_instance_id",
                    "space": "$space"
                }
            },
            "spec": {
                "type": "NodePort",
                "ports": [
                    {
                        "name": "",
                        "protocol": "TCP",
                        "port": 8080,
                        "targetPort": 0,
                        "nodePort": 0
                    }
                ],
                "selector": {
                    "instance_id": "$instance_id"
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
            "metadata":
                {
                    "name": "$short_instance_id",
                    "creationTimestamp": None,
                    "labels":
                        {
                            "instance_id": "$instance_id",
                            "managed_by": "TAP",
                            "org": "$org",
                            "short_instance_id": "$short_instance_id",
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
                "name": "$short_instance_id-gateway-args",
                "creationTimestamp": None,
                "labels": {
                    "instance_id": "$instance_id",
                    "managed_by": "TAP",
                    "org": "$org",
                    "short_instance_id": "$short_instance_id",
                    "space": "$space"
                }
            },
            "data": {
                "id": "ZzE=",
                "index": "MA==",
                "pub.ack": "ZmFsc2U=",
                "pub.compress": "dHJ1ZQ==",
                "pub.flushfreq": "MQ==",
                "pub.topic": "bWVzc2FnZXM=",
                "pub.uri": "a2Fma2EtbW9jazo5MDky",
                "server.authmethod": "bm9uZQ==",
                "server.devicekeysuri": "",
                "server.host": "MC4wLjAuMA==",
                "server.port": "ODA4MA==",
                "server.root": "L3dz",
                "server.token": "",
                "server.tolerablejwtage": "NQ==",
                "trace": "dHJ1ZQ=="
            }
        }
    ]
}]

etcd_template = {
    "body": [{
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
                                    "image": "$repository_uri/coreos/etcd:v3.0.10",
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
    }],
    "hooks": None
}
sample_python_app_offering = {
    "body": [{
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
                    "name": "sample-python-app",
                    "ports": [
                      {
                        "containerPort": 80,
                        "protocol": "TCP"
                      },
                    ],
                    "env": [
                      {
                        "name": "MANAGED_BY",
                        "value": "TAP"
                      },
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
                "name": "transport",
                "protocol": "TCP",
                "port": 80,
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
    }],
    "hooks": None
  }

nats_template = {
    "body": [{
        "componentType": "instance",
        "persistentVolumeClaims": None,
        "deployments": [{
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
                        "containers": [{
                            "name": "k-nats",
                            "image": "$repository_uri/nats:0.8.1",
                            "ports": [{
                                "containerPort": 4222,
                                "protocol": "TCP"
                            },
                            {
                                "containerPort": 8333,
                                "protocol": "TCP"
                            }],
                            "env": [{
                                "name": "MANAGED_BY",
                                "value": "TAP"
                            },
                            {
                                "name": "NATS_PASSWORD",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "Name": "$short_instance_id-nats-credentials",
                                        "key": "nats-password"
                                    }
                                }
                            },
                            {
                                "name": "NATS_USERNAME",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "Name": "$short_instance_id-nats-credentials",
                                        "key": "nats-username"
                                    }
                                }
                            }],
                            "resources": {
                                "limits": {
                                    "memory": "500M"
                                },
                                "requests": {
                                    "memory": "100M"
                                }
                            },
                            "imagePullPolicy": "IfNotPresent"
                        }],
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
        }],
        "ingresses": None,
        "services": [{
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
                "ports": [{
                    "name": "rest",
                    "protocol": "TCP",
                    "port": 4222,
                    "targetPort": 0,
                    "nodePort": 0
                },
                {
                    "name": "transport",
                    "protocol": "TCP",
                    "port": 8333,
                    "targetPort": 0,
                    "nodePort": 0
                }],
                "selector": {
                    "instance_id": "$instance_id"
                }
            },
            "status": {
                "loadBalancer": {

                }
            }
        }],
        "serviceAccounts": [{
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
        }],
        "secrets": [{
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": "$short_instance_id-nats-credentials",
                "creationTimestamp": None,
                "labels": {
                    "idx_and_short_instance_id": "$idx_and_short_instance_id",
                    "managed_by": "TAP",
                    "instance_id": "$instance_id"
                }
            },
            "data": {
                "nats-password": "$base64-$random1",
                "nats-username": "$base64-$random2"
            }
        }],
        "configMaps": [{
            "kind": "ConfigMap",
            "apiVersion": "v1",
            "metadata": {
                "name": "$short_instance_id-nats-credentials",
                "creationTimestamp": None,
                "labels": {
                    "idx_and_short_instance_id": "$idx_and_short_instance_id",
                    "managed_by": "TAP",
                    "instance_id": "$instance_id"
                }
            },
            "data": {
                "nats-password": "$base64-$random1",
                "nats-username": "$base64-$random2"
            }
        }]
    }],
    "hooks": None
}