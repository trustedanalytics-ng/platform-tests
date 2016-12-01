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
import yaml
import config

from modules import file_utils
from modules.ssh_lib import JumpClient
from .. import HttpClientConfiguration, HttpClientType


class KubernetesConfigurationProvider(object):
    _AUTH_USERNAME = config.ng_k8s_service_auth_username
    _SOCKS_PROXY = "socks5://localhost:{}".format(config.ng_socks_proxy_port)
    _KUBE_DIR_NAME = ".kube"
    _KUBE_CONFIG_FILE_NAME = "config"
    _kube_dir_path = None
    _certificate = None
    _host = None
    _api_version = None

    @classmethod
    def get(cls, rest_prefix="api", api_version="v1"):
        """
        When called for the first time, retrieve kubernetes service configuration from jumpbox.
        """

        if rest_prefix is None:
            rest_prefix = "api"
        if cls._kube_dir_path is None:
            cls._kube_dir_path = cls._download_config_directory()
            kube_config_path = os.path.join(cls._kube_dir_path, cls._KUBE_CONFIG_FILE_NAME)
            cls._host = cls._get_url(kube_config_path)
            cls._certificate = cls._get_certificates(cls._kube_dir_path, kube_config_path)
            cls._api_version = cls._get_api_version(kube_config_path)

        if api_version is not None:
            cls._api_version = api_version

        client_configuration = HttpClientConfiguration(
            client_type=HttpClientType.NO_AUTH,
            url="{}/{}/{}".format(cls._host, rest_prefix, cls._api_version),
            proxies={"http": cls._SOCKS_PROXY, "https": cls._SOCKS_PROXY},
            cert=cls._certificate
        )

        return client_configuration

    @classmethod
    def _download_config_directory(cls) -> str:
        jump_client = JumpClient(username=config.ng_jump_user_with_kubectl_config)
        target_directory = file_utils.TMP_FILE_DIR
        jump_client.scp_from_remote(source_path=cls._KUBE_DIR_NAME, target_path=target_directory)
        local_kube_dir_path = os.path.join(target_directory, cls._KUBE_DIR_NAME)
        assert os.path.exists(local_kube_dir_path), "Failed download {} to {}".format(cls._KUBE_DIR_NAME,
                                                                                      local_kube_dir_path)
        return local_kube_dir_path

    @staticmethod
    def _get_url(yaml_path) -> str:
        with open(yaml_path) as f:
            kube_config = yaml.load(f)
        return kube_config["clusters"][0]["cluster"]["server"]

    @staticmethod
    def _get_api_version(yaml_path) -> str:
        with open(yaml_path) as f:
            kube_config = yaml.load(f)
        return kube_config["apiVersion"]

    @classmethod
    def _get_certificates(cls, kube_dir_path, yaml_path) -> tuple:
        with open(yaml_path) as f:
            kube_config = yaml.load(f)
        user_config = next((item for item in kube_config["users"] if item["name"] == cls._AUTH_USERNAME), None)
        assert user_config is not None, "Configuration not found for user {}".format(cls._AUTH_USERNAME)
        client_certificate = user_config["user"]["client-certificate"]
        client_key = user_config["user"]["client-key"]
        client_certificate_path = os.path.join(kube_dir_path, client_certificate)
        client_key_path = os.path.join(kube_dir_path, client_key)
        assert os.path.isfile(client_certificate_path), "No such file {}".format(client_certificate_path)
        assert os.path.isfile(client_key_path), "No such file {}".format(client_key_path)
        return client_certificate_path, client_key_path
