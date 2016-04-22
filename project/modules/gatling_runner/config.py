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
    """Gatling runner package configuration."""

    # Download directory for getting gatling packages
    DOWNLOAD_DIRECTORY = os.path.join(os.path.dirname(__file__), "download")

    # Gatling package repository default settings
    REPO_URL = ""
    REPO_NAME = "performance-tests"
    REPO_VERSION = "0.0.3"

    # Gatling ssh connector default settings
    SSH_PORT = 22
    SSH_USERNAME = "ubuntu"
    SSH_HOST = ""

    # Gatling tests connection proxy settings
    GATLING_PROXY = "proxy-mu.intel.com"
    GATLING_PROXY_HTTP_PORT = 911
    GATLING_PROXY_HTTPS_PORT = 912

    # How long (in seconds) to wait before make next gatling results check
    TIME_BEFORE_NEXT_TRY = 300

    # How many times try to get gatling logs when log file size not change
    NUMBER_OF_TRIALS_WITHOUT_LOG_CHANGE = 2

    @classmethod
    def gatling_ssh_username(cls):
        """Gatling ssh username."""
        return CONFIG["gatling_ssh_username"] \
            if "gatling_ssh_username" in CONFIG else cls.SSH_USERNAME

    @classmethod
    def gatling_ssh_host(cls):
        """Gatling ssh remote host."""
        return CONFIG["gatling_ssh_host"] \
            if "gatling_ssh_host" in CONFIG else cls.SSH_HOST

    @classmethod
    def gatling_ssh_port(cls):
        """Gatling ssh remote port."""
        return CONFIG["gatling_ssh_port"] \
            if "gatling_ssh_port" in CONFIG else cls.SSH_PORT

    @staticmethod
    def gatling_ssh_key_path():
        """Path to gatling ssh key."""
        key_path = CONFIG["gatling_ssh_key_path"] \
            if "gatling_ssh_key_path" in CONFIG else CONFIG["cdh_key_path"]
        return os.path.expanduser(key_path)

    @classmethod
    def number_of_trials_without_log_change(cls):
        """ Returns number of retries for getting gatling results. """
        return CONFIG["gatling_number_of_trials_without_log_change"] \
            if "gatling_number_of_trials_without_log_change" in CONFIG else cls.NUMBER_OF_TRIALS_WITHOUT_LOG_CHANGE

    @classmethod
    def gatling_repo_url(cls):
        """Gatling package repository url address."""
        return CONFIG["gatling_repo_url"] \
            if "gatling_repo_url" in CONFIG else cls.REPO_URL

    @classmethod
    def gatling_repo_name(cls):
        """Gatling package name."""
        return CONFIG["gatling_repo_name"] \
            if "gatling_repo_name" in CONFIG else cls.REPO_NAME

    @classmethod
    def gatling_repo_version(cls):
        """Gatling package version."""
        return CONFIG["gatling_repo_version"] \
            if "gatling_repo_version" in CONFIG else cls.REPO_VERSION

    @classmethod
    def gatling_package_file_name(cls):
        """Gatling package file name."""
        return "{}-{}.jar".format(
            cls.gatling_repo_name(),
            cls.gatling_repo_version()
        )

    @classmethod
    def gatling_package_file_url(cls):
        """Gatling package url address."""
        return "{}{}/{}/{}".format(
            cls.gatling_repo_url(),
            cls.gatling_repo_name(),
            cls.gatling_repo_version(),
            cls.gatling_package_file_name()
        )

    @classmethod
    def gatling_package_file_path(cls):
        """Path to gatling package file."""
        return os.path.join(cls.DOWNLOAD_DIRECTORY, cls.gatling_package_file_name())
