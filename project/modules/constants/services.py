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


class ServiceLabels(object):
    ARANGODB = "arangodb-22"
    ATK = "atk"
    CASSANDRA22 = "cassandra-22"
    CASSANDRA33 = "cassandra-33"
    CDH = "cdh"
    CONSUL = "consul-031"
    COUCH_DB = "couchdb-16"
    ELASTICSEARCH13 = "elasticsearch-13"
    ELASTICSEARCH17 = "elasticsearch-17"
    ELASTICSEARCH17_MULTINODE = "elasticsearch17-multinode"
    ELK_MULTINODE = "elk-multinode"
    ETCD = "etcd"
    GATEWAY = "gateway"
    GEARPUMP = "gearpump-080"
    GEARPUMP_DASHBOARD = "gearpump-dashboard"
    H2O = "h2o-350"
    HBASE = "hbase"
    HDFS = "hdfs"
    HIVE = "hive"
    INFLUX_DB_088 = "influxdb-088"
    INFLUX_DB_110 = "influxdb-110"
    JUPYTER = "jupyter"
    KAFKA = "kafka"
    KERBEROS = "kerberos-113"
    LOGSTASH = "logstash-14"
    MEMCACHED = "memcached-14"
    MONGO_DB_30 = "mongodb-30"
    MONGO_DB_30_MULTINODE = "mongodb30-multinode"
    MOSQUITTO = "mosquitto-14"
    MYSQL = "mysql-56"
    MYSQL_MULTINODE = "mysql56-multinode"
    NATS = "nats"
    NEO4J = "neo4j-21"
    ORIENT_DB = "orientdb-212"
    ORIENT_DB_DASHBOARD = "orientdb-dashboard"
    PSQL = "postgresql-93"
    PSQL94_MULTINODE = "postgresql94-multinode"
    RABBIT_MQ = "rabbitmq-36"
    REDIS = "redis-30"
    RETHINK_DB = "rethinkdb"
    RSTUDIO = "rstudio"
    SCORING_ENGINE = "scoring-engine"
    SCORING_PIPELINES = "scoring-pipelines"
    SEAHORSE = "seahorse"
    SMTP = "smtp"
    YARN = "yarn"
    ZOOKEEPER = "zookeeper"
    ZOOKEEPER_WSSB = "zookeeper-wssb"


class ServicePlan(object):
    BARE = "bare"
    CLUSTERED = "clustered"
    CLUSTERED_PERSISTENT = "clustered persistent"
    CREATE_USER_DIRECTORY = "create-user-directory"
    ENCRYPTED = "encrypted"
    ENCRYPTED_DIR = "encrypted-dir"
    FREE = "free"
    GET_USER_DIRECTORY = "get-user-directory"
    MEDIUM = "medium"
    MULTITENANT = "multitenant"
    ORG_SHARED = "org-shared"
    PERSISTENT = "persistent"
    PLAIN_DIR = "plain-dir"
    SHARED = "shared"
    SIMPLE = "simple"
    SIMPLE_ATK = "Simple"
    SINGLE = "single"
    SINGLE_SMALL = "single-small"
    SINGLE_MEDIUM = "single-medium"
    SMALL = "small"
    STANDARD = "standard"
    WORKER_1 = "1_worker"
    WORKER_2 = "2_workers"
    WORKER_3 = "3_workers"
    MEM128MB = "128Mb"
    MEM256MB = "256Mb"
    MEM512MB = "512Mb"


class ParametrizedService(object):

    parametrized_offerings = {
        ServiceLabels.SCORING_ENGINE: True,                  # all plans
        ServiceLabels.GEARPUMP_DASHBOARD: True,              # all plans
        ServiceLabels.HDFS: ServicePlan.GET_USER_DIRECTORY,  # only one plan
    }

    @classmethod
    def is_parametrized(cls, label: ServiceLabels, plan_name: ServicePlan):
        parametrized_plan = cls.parametrized_offerings.get(label)
        return parametrized_plan is True or plan_name == parametrized_plan


class ServiceTag(object):
    K8S = "k8s"
