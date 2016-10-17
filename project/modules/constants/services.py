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
    ARANGODB = "arangodb22"
    ATK = "atk"
    CASSANDRA21 = "cassandra21"
    CDH = "cdh"
    CONSUL = "consul"
    COUCH_DB = "couchdb16"
    ELASTICSEARCH = "elasticsearch13"
    ELASTICSEARCH17_MULTINODE = "elasticsearch17-multinode"
    ELK_MULTINODE = "elk-multinode"
    ETCD = "etcd"
    GATEWAY = "gateway"
    GEARPUMP = "gearpump"
    GEARPUMP_DASHBOARD = "gearpump-dashboard"
    H2O = "h2o"
    HBASE = "hbase"
    HDFS = "hdfs"
    HIVE = "hive"
    INFLUX_DB = "influxdb088"
    JUPYTER = "jupyter"
    KAFKA = "kafka"
    KERBEROS = "kerberos"
    LOGSTASH = "logstash14"
    MEMCACHED = "memcached14"
    MONGO_DB = "mongodb26"
    MONGO_DB_30_MULTINODE = "mongodb30-multinode"
    MOSQUITTO = "mosquitto14"
    MYSQL = "mysql56"
    MYSQL_MULTINODE = "mysql56-multinode"
    NATS = "nats"
    NEO4J = "neo4j21"
    ORIENT_DB = "orientdb"
    ORIENT_DB_DASHBOARD = "orientdb-dashboard"
    PSQL = "postgresql93"
    PSQL94_MULTINODE = "postgresql94-multinode"
    RABBIT_MQ = "rabbitmq36"
    REDIS = "redis30"
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
    FREE = "free"
    GET_USER_DIRECTORY = "get-user-directory"
    MULTITENANT = "multitenant"
    PERSISTENT = "persistent"
    SHARED = "shared"
    SIMPLE = "simple"
    SIMPLE_ATK = "Simple"
    WORKER_1 = "1 worker"
    WORKER_2 = "2 workers"
    WORKER_3 = "3 workers"
    MEM128MB = "128Mb"


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
