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

from configuration.config import CONFIG


class Config(object):
    """Http client module main configuration."""

    @staticmethod
    def auth_basic_token_url():
        """Url address to auth basic token service."""
        return CONFIG["auth_basic_token_url"] \
            if "auth_basic_token_url" in CONFIG \
            else "https://login.{}/oauth/token".format(CONFIG["domain"])

    @staticmethod
    def auth_uaa_token_url():
        """Url address to auth uaa token service."""
        return CONFIG["auth_uaa_token_url"] \
            if "auth_uaa_token_url" in CONFIG \
            else "http://uaa.{}/oauth/token".format(CONFIG["domain"])

    @staticmethod
    def auth_login_url():
        """Url address to auth login service."""
        return CONFIG["auth_login_url"] \
            if "auth_login_url" in CONFIG \
            else "{}://login.{}/".format(CONFIG["login.do_scheme"], CONFIG["domain"])

    @staticmethod
    def service_uaa_url():
        """Uaa service url."""
        return CONFIG["service_uaa_url"] \
            if "service_uaa_url" in CONFIG \
            else "http://uaa.{}/".format(CONFIG["domain"])

    @staticmethod
    def template_application_url():
        """Application template url."""
        return CONFIG["template_application_url"] \
            if "template_application_url" in CONFIG \
            else "http://{}.{}/".format("application_name", CONFIG["domain"])

    @staticmethod
    def service_cloud_foundry_url():
        """Cloud foundry service url."""
        return CONFIG["service_cloud_foundry_url"] \
            if "service_cloud_foundry_url" in CONFIG \
            else "https://api.{}/v2/".format(CONFIG["domain"])

    @staticmethod
    def service_application_broker_url():
        """Application broker service url."""
        return CONFIG["service_application_broker_url"] \
            if "service_application_broker_url" in CONFIG \
            else "http://application-broker.{}/{}/".format(CONFIG["domain"], CONFIG["cf_api_version"])

    @staticmethod
    def service_kubernetes_broker_basic_url():
        """Kubernetes broker service basic url."""
        return CONFIG["service_application_broker_url"] \
            if "service_kubernetes_broker_url" in CONFIG \
            else "http://kubernetes-broker.{}/{}/".format(CONFIG["domain"], CONFIG["cf_api_version"])

    @staticmethod
    def service_kubernetes_broker_token_url():
        """Kubernetes broker service token url."""
        return CONFIG["service_application_broker_url"] \
            if "service_kubernetes_broker_url" in CONFIG \
            else "http://kubernetes-broker.{}/".format(CONFIG["domain"])

    @staticmethod
    def service_demiurge_url():
        """Demiurge service url."""
        return CONFIG["service_demiurge_url"] \
            if "service_demiurge_url" in CONFIG \
            else "http://demiurge.{}/".format(CONFIG["domain"])

    @staticmethod
    def service_console_url():
        """Console service url."""
        return CONFIG["service_console_url"] \
            if "service_console_url" in CONFIG \
            else "https://console.{}".format(CONFIG["domain"])
