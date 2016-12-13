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

import config


class Config(object):

    # Remote logger check whether tunnel need be opened or not
    TUNNEL_AVAILABLE = False

    # Root directory for storing remote log files
    ROOT_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")

    # Log file name format
    LOG_FILE_NAME = "{}.log"

    # How long (in seconds) to wait before make request to elastic search
    TIME_BEFORE_NEXT_CALL = 15

    # Elastic search url address
    ELASTIC_QUERY_URL = "http://{}:{}/logstash-{}/_search"

    # Elastic search host
    # do not change empty value.
    # value is updated automatically after connection with master
    ELASTIC_SEARCH_HOST = ''

    ELASTIC_SEARCH_HOST_PORT = 9200

    # How long (in seconds) to wait for elastic search api to send data before giving up
    ELASTIC_SEARCH_REQUEST_TIMEOUT = 120

    ELASTIC_SEARCH_SSH_TUNNEL_KEY_PATH = config.jumpbox_key_path

    REMOTE_LOGGER_RETRY_COUNT = config.logsearch_collect_retry_count

    ELASTIC_SEARCH_SSH_TUNNEL_HOST = config.jumpbox_hostname
    
    JUMPBOX_KEY_PATH = config.jumpbox_key_path
    
    JUMPBOX_HOST = config.jumpbox_hostname

