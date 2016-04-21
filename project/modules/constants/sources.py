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

class CfEnvApp:
    repo_name = "cf-env"
    repo_owner = "cloudfoundry-community"
    # older commit where the app uses version of Ruby compatible with TAP cf version < 222
    commit_id = "f36c111"


class TapGitHub:

    intel_data = "intel-data"
    trustedanalytics = "trustedanalytics"

    apployer = "apployer"
    appstack_path = "appstack.yml"
    hbase_api_example = "hbase-java-api-example"
    kafka2hdfs = "kafka2hdfs"
    mqtt_demo = "mqtt-demo"
    sql_api_example = "sql-api-example"
    ws_kafka_hdfs = "ingestion-ws-kafka-hdfs"
    ws2kafka = "ws2kafka"
