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


class TapComponent:
    auth_gateway = "auth-gateway"
    app_dependency_discoverer = "app-dependency-discoverer"
    console = "console"
    cdh_broker = "cdh-broker"
    das = "data-acquisition"
    data_catalog = "data-catalog"
    dataset_publisher = "dataset-publisher"
    demiurge = "demiurge"
    gearpump_broker = "gearpump-broker"
    gearpump_dashboard = "gearpump-dashboard"
    h2o_broker = "h2o-broker"
    h2o_scoring_engine_publisher = "h2o-engines-publisher"
    hbase_broker = "hbase-broker"
    hdfs_broker = "hdfs-broker"
    downloader = "downloader"
    uploader = "uploader"
    hive_broker = "hive-broker"
    kafka_broker = "kafka-broker"
    kerberos_service = "kerberos-service"
    kubernetes_broker = "kubernetes-broker"
    latest_events_service = "latest-events-service"
    metadata_parser = "metadata-parser"
    metrics_grafana = "metrics-grafana"
    model_catalog = "model-catalog"
    platform_snapshot = "platform-snapshot"
    platform_tests = "platform-tests"
    platform_operations = "platform-operations"
    router_metrics_provider = "router-metrics-provider"
    service_catalog = "service-catalog"
    service_exposer = "service-exposer"
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
    api_service = "api"
    blob_store = "blob-store"
    ca = "ca"
    catalog = "catalog"
    container_broker = "container-broker"
    h2o_model_provider = "h2o-model-provider"
    image_factory = "image-factory"
    key_counter = "key-counter"
    metrics_collector_ambassador = "metrics-collector-ambassador"
    metrics_presenter = "metrics-presenter"
    metrics_prometheus = "metrics-prometheus"
    metrics_tap_catalog_collector = "metrics-tap-catalog-collector"
    monitor = "monitor"
    nginx_ingress = "tapingress"
    template_repository = "template-repository"
    uaa_client_register_job = "tap-uaa-client-register-job"
    uaa = "uaa"

    cli = "cli"  # not a HTTP service, but a command-line utility

    # ---- TAP NG components - 3rd party ---- #
    image_repository = "image-repository"
    message_queue = "queue"

    @classmethod
    def get_list_internal(cls):
        return [cls.blob_store, cls.key_counter, cls.catalog, cls.container_broker, cls.das,
                cls.data_catalog, cls.dataset_publisher, cls.h2o_scoring_engine_publisher,
                cls.downloader, cls.uploader, cls.image_factory, cls.metadata_parser,
                cls.metrics_grafana, cls.metrics_prometheus, cls.model_catalog, cls.nginx_ingress,
                cls.template_repository, cls.user_management]

    @classmethod
    def get_list_all(cls):
        return cls.get_list_internal() + [cls.api_service, cls.console]
