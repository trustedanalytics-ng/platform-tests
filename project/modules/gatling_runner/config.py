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
    """Gatling runner package configuration."""

    # Download directory for getting gatling packages
    DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(__file__), "download")

    # Gatling package repository default settings
    GATLING_REPO_URL = os.environ.get("GATLING_REPO_URL")
    GATLING_REPO_NAME = os.environ.get("GATLING_REPO_NAME")
    GATLING_REPO_VERSION = os.environ.get("GATLING_REPO_VERSION")

    # Gatling ssh connector default settings
    GATLING_SSH_PORT = os.environ.get("GATLING_SSH_PORT")
    GATLING_SSH_USERNAME = os.environ.get("GATLING_SSH_USERNAME")
    GATLING_SSH_HOST = os.environ.get("GATLING_SSH_HOST")
    GATLING_SSH_KEY_PATH = os.environ.get("GATLING_SSH_KEY_PATH", config.jumpbox_key_path)

    # Gatling tests connection proxy settings
    GATLING_PROXY = os.environ.get("GATLING_PROXY")
    GATLING_PROXY_HTTP_PORT = config.get_int("GATLING_PROXY_HTTP_PORT")
    GATLING_PROXY_HTTPS_PORT = config.get_int("GATLING_PROXY_HTTPS_PORT")

    # How long (in seconds) to wait before make next gatling results check
    TIME_BEFORE_NEXT_TRY = 300

    # How many times try to get gatling logs when log file size not change
    NUMBER_OF_TRIALS_WITHOUT_LOG_CHANGE = 2

    GATLING_PACKAGE_FILE_NAME = "{}-{}.jar".format(GATLING_REPO_NAME, GATLING_REPO_VERSION)
    GATLING_PACKAGE_FILE_URL = "{}{}/{}/{}".format(GATLING_REPO_URL, GATLING_REPO_NAME, GATLING_REPO_VERSION,
                                                   GATLING_PACKAGE_FILE_NAME)
    GATLING_PACKAGE_FILE_PATH = os.path.join(DOWNLOAD_DIRECTORY, GATLING_PACKAGE_FILE_NAME)

