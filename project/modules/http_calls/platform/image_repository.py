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

import config

from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import ProxiedConfigurationProvider


def _get_client():
    configuration = ProxiedConfigurationProvider.get("http://{}/v2".format(config.ng_image_repository_url))
    return HttpClientFactory.get(configuration)


def get_image_repositories():
    response = _get_client().request(HttpMethod.GET,
                                     path="_catalog",
                                     msg="IMAGE REPOSITORY: get repositories")
    return response
