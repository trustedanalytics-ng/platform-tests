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

import os


class TapGitHub:

    intel_data = "intel-data"
    trustedanalytics = "trustedanalytics"

    apployer = "apployer"
    appstack_path = "appstack.yml"
    dataset_reader_sample = "dataset-reader-sample"
    hbase_api_example = "hbase-java-api-example"
    kafka2hdfs = "kafka2hdfs"
    mqtt_demo = "mqtt-demo"
    sql_api_example = "sql-api-example"
    ws_kafka_hdfs = "ingestion-ws-kafka-hdfs"
    ws2kafka = "ws2kafka"
    space_shuttle_demo = "space-shuttle-demo"
    hdfs_hive_demo = "hdfs-hive-demo"

    # TAP NG repositories
    ilab_deploy = "tapng-ilab-deploy"


class RelativeRepositoryPaths:

    space_shuttle_model_input_data = os.path.join("src", "main", "client", "shuttle_scale_cut_val.csv")
    space_shuttle_model_generator = os.path.join("src", "main", "atkmodelgenerator", "atk_model_generator.py")

    # Path to the private ssh key for TAP NG environments - in tapng-ilab-deploy repository
    ilab_centos_key = "id_rsa"
