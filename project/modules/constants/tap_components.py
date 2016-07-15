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

from enum import Enum


class TapComponent(Enum):
    auth_gateway = "auth-gateway"
    auth_proxy = "auth-proxy"
    app_dependency_discoverer = "app-dependency-discoverer"
    app_launcher_helper = "app-launcher-helper"
    application_broker = "application-broker"
    console = "console"
    cdh_broker = "cdh-broker"
    das = "das"
    data_catalog = "data-catalog"
    dataset_publisher = "dataset-publisher"
    demiurge = "demiurge"
    gearpump_broker = "gearpump-broker"
    gearpump_dashboard = "gearpump-dashboard"
    h2o_broker = "h2o-broker"
    h2o_scoring_engine_publisher = "h2o-scoring-engine-publisher"
    hbase_broker = "hbase-broker"
    hdfs_broker = "hdfs-broker"
    hdfs_downloader = "hdfs-downloader"
    hdfs_uploader = "hdfs-uploader"
    hive_broker = "hive-broker"
    kafka_broker = "kafka-broker"
    kerberos_service = "kerberos-service"
    kubernetes_broker = "kubernetes-broker"
    latest_events_service = "latest-events-service"
    metadata_parser = "metadataparser"
    metrics_provider = "metrics-provider"
    model_catalog = "model-catalog"
    platform_context = "platform-context"
    platform_snapshot = "platform-snapshot"
    platform_tests = "platform-tests"
    platform_operations = "platform-operations"
    router_metrics_provider = "router-metrics-provider"
    service_catalog = "service-catalog"
    service_exposer = "service-exposer"
    smtp = "smtp"
    smtp_broker = "smtp-broker"
    user_management = "user-management"
    workflow_scheduler = "workflow-scheduler"
    yarn_broker = "yarn-broker"
    zookeeper_broker = "zookeeper-broker"
    zookeeper_wssb_broker = "zookeeper-wssb-broker"

    ingestion_ws_kafka_hdfs = "ingestion-ws-kafka-hdfs"
    ingestion_ws_kafka_gearpump_hbase = "ingestion-ws-kafka-gearpump-hbase"
    mqtt_demo = "mqtt-demo"
    dataset_reader = "dataset-reader"

    atk = "atk"
    gateway = "gateway"
    scoring_engine = "scoring-engine"

    space_shuttle_demo = "space-shuttle-demo"

    # ---- TAP NG components ---- #
    blob_store = "blob-store"
    catalog = "catalog"
    console_service = "console-service"
    container_broker = "container-broker"
    dashboard = "dashboard"
    image_factory = "image-factory"
    template_repository = "template-repository"

    @classmethod
    def names(cls):
        return [i.name for i in list(cls)]

    @classmethod
    def values(cls):
        return [i.value for i in list(cls)]

