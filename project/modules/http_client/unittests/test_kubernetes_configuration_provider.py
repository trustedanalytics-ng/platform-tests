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
from unittest import mock

from modules.http_client.configuration_provider.kubernetes import KubernetesConfigurationProvider


class TestKubernetesConfigurationProvider:
    TEST_ADMIN_USERNAME = "test-username"
    TEST_URL = "https://bla.bla.bla:443"
    TEST_CERT_FILE_NAME = "test-username.crt"
    TEST_KEY_FILE_NAME = "test-username.key"
    TEST_API_VERSION = "test-version"
    EXAMPLE_CUBE_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                            "fixtures",
                                                            "example_kube_config"))

    ISFILE = "modules.http_client.configuration_provider.kubernetes.os.path.isfile"

    def test_get_url(self):
        test_url = KubernetesConfigurationProvider._get_url(self.EXAMPLE_CUBE_CONFIG_PATH)
        assert test_url == self.TEST_URL

    def test_get_api_version(self):
        test_api_version = KubernetesConfigurationProvider._get_api_version(self.EXAMPLE_CUBE_CONFIG_PATH)
        assert test_api_version == self.TEST_API_VERSION

    @mock.patch.object(KubernetesConfigurationProvider, "_AUTH_USERNAME", TEST_ADMIN_USERNAME)
    @mock.patch(ISFILE, mock.Mock(return_value=True))
    def test_get_certificate(self):
        test_kube_dir_path = "/test/path"
        test_cert = KubernetesConfigurationProvider._get_certificates(test_kube_dir_path, self.EXAMPLE_CUBE_CONFIG_PATH)
        assert test_cert[0] == os.path.join(test_kube_dir_path, self.TEST_CERT_FILE_NAME)
        assert test_cert[1] == os.path.join(test_kube_dir_path, self.TEST_KEY_FILE_NAME)
