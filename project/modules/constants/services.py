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
    CDH = "cdh"
    COUCH_DB = "couchdb16"
    ELASTICSEARCH = "elasticsearch13"
    ETCD = "etcd"
    GATEWAY = "gateway"
    GEARPUMP = "gearpump"
    GEARPUMP_DASHBOARD = "gearpump-dashboard"
    H2O = "h2o"
    HBASE = "hbase"
    HDFS = "hdfs"
    INFLUX_DB = "influxdb088"
    IPYTHON = "ipython"
    KAFKA = "kafka"
    LOGSTASH = "logstash14"
    MEMCACHED = "memcached14"
    MONGO_DB = "mongodb26"
    MOSQUITTO = "mosquitto14"
    MYSQL = "mysql56"
    NATS = "nats"
    NEO4J = "neo4j21"
    PSQL = "postgresql93"
    RABBIT_MQ = "rabbitmq33"
    REDIS = "redis28"
    RETHINK_DB = "rethinkdb"
    RSTUDIO = "rstudio"
    SCORING_ENGINE = "scoring-engine"
    SMTP = "smtp"
    YARN = "yarn"
    ZOOKEEPER = "zookeeper"
    ZOOKEEPER_WSSB = "zookeeper-wssb"


PARAMETRIZED_SERVICE_INSTANCES = [ServiceLabels.SCORING_ENGINE, ServiceLabels.GEARPUMP_DASHBOARD]

