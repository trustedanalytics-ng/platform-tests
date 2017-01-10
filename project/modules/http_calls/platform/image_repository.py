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

from tap_component_config import third_party_services
from modules.constants import TapComponent as TAP
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sSecureServiceConfigurationProvider


def _get_client():
    image_repository_config = third_party_services[TAP.image_repository]
    service_url = image_repository_config.get("url")
    if not service_url:
        service_url = K8sSecureServiceConfigurationProvider.get_service_url(
                service_name=image_repository_config["kubernetes_service_name"],
                namespace=image_repository_config["kubernetes_namespace"])
    configuration = K8sSecureServiceConfigurationProvider.get(service_url=service_url,
                                                              api_version=image_repository_config["api_version"])
    return HttpClientFactory.get(configuration)


def get_image_repositories():
    response = _get_client().request(HttpMethod.GET,
                                     path="_catalog",
                                     msg="IMAGE REPOSITORY: get repositories")
    return response
