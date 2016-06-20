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

from configuration.config import CONFIG


class Config(object):

    # Root directory for storing remote log files
    ROOT_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")

    # Log file name format
    LOG_FILE_NAME = "{}.log"

    # How long (in seconds) to wait before make request to elastic search
    TIME_BEFORE_NEXT_CALL = 15

    # Ssh tunnel configuration - local port
    ELASTIC_SSH_TUNNEL_LOCAL_PORT = 9200

    # Ssh tunnel configuration - elastic search url address
    ELASTIC_SSH_TUNNEL_URL = "http://localhost:{}/logstash-{}/_search"

    # Ssh tunnel configuration - remote username
    ELASTIC_SSH_TUNNEL_USER = "ubuntu"

    # Elastic search host
    ELASTIC_SEARCH_HOST = "10.0.7.10"

    # Elastic search port
    ELASTIC_SEARCH_PORT = 9200

    # How long (in seconds) to wait for elastic search api to send data before giving up
    ELASTIC_SEARCH_REQUEST_TIMEOUT = 120

    @staticmethod
    def is_remote_logger_enabled():
        """ Returns if remote logger is enabled or disabled. """
        return CONFIG["remote_log_enabled"] if "remote_log_enabled" in CONFIG else True

    @staticmethod
    def get_number_of_trials():
        """ Returns number of retries for getting elastic search response. """
        return CONFIG["remote_logger_retry_count"] if "remote_logger_retry_count" in CONFIG else 5

    @staticmethod
    def get_elastic_ssh_tunnel_host():
        """ Returns ssh tunnel remote host. """
        if CONFIG["jumpbox_address"] is not None:
            return CONFIG["jumpbox_address"]
        return "jump.{}".format(CONFIG["domain"])

    @staticmethod
    def get_elastic_ssh_tunnel_key_path():
        """ Returns ssh tunnel path to ssh key. """
        return CONFIG["cdh_key_path"]
