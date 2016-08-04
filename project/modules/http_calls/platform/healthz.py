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

from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from modules.constants import HttpStatus


def _get_client(service_name):
    configuration = K8sServiceConfigurationProvider.get(service_name=service_name, api_endpoint="healthz")
    return HttpClientFactory.get(configuration)


def get(service_name):
    """ GET """
    response = _get_client(service_name).request(HttpMethod.GET, raw_response=True, path="")
    assert response.status_code == HttpStatus.CODE_OK
    return response
