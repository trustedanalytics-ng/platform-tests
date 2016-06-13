#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License";
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

from ..http_client.configuration_provider.demiurge import DemiurgeConfigurationProvider
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.http_client_factory import HttpClientFactory


def demiurge_get_clusters():
    """GET /clusters"""
    return HttpClientFactory.get(DemiurgeConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="clusters",
        msg="DEMIURGE: get list of clusters"
    )


def demiurge_get_cluster(cluster_name):
    """GET /clusters/{cluster_name}"""
    return HttpClientFactory.get(DemiurgeConfigurationProvider.get()).request(
        method=HttpMethod.GET,
        path="clusters/{}".format(cluster_name),
        msg="DEMIURGE: get cluster"
    )

def demiurge_create_cluster(cluster_name):
    """PUT /clusters/{cluster_name}"""
    return HttpClientFactory.get(DemiurgeConfigurationProvider.get()).request(
        method=HttpMethod.PUT,
        path="clusters/{}".format(cluster_name),
        msg="DEMIURGE: create cluster"
    )
