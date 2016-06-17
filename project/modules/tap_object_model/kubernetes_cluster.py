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

from retry import retry

from modules.constants import TapComponent as TAP
from modules.http_calls import cloud_foundry as cf, demiurge


class KubernetesCluster(object):
    wait_before_remove_cluster_sec = 0

    def __init__(self, name, api_server, consul_http_api, username, password):
        """Cluster name is it's org guid"""
        self.name = name
        self.api_server = api_server
        self.consul_http_api = consul_http_api
        self.username = username
        self.password = password

    @classmethod
    def _from_demiurge_response(cls, cluster_info):
        return cls(name=cluster_info["cluster_name"], api_server=cluster_info["api_server"],
                   consul_http_api=cluster_info["consul_http_api"], username=cluster_info["username"],
                   password=cluster_info["password"])

    @classmethod
    def demiurge_api_get_list(cls):
        response = demiurge.demiurge_get_clusters()
        clusters = []
        for cluster_info in response:
            cluster = cls._from_demiurge_response(cluster_info)
            clusters.append(cluster)
        return clusters

    @classmethod
    @retry(AssertionError, tries=180, delay=5)
    def demiurge_api_get(cls, name):
        response = demiurge.demiurge_get_cluster(cluster_name=name)
        if response == "":
            raise AssertionError("Cluster {} not found".format(name))
        return cls._from_demiurge_response(cluster_info=response)

    @classmethod
    def demiurge_api_create(cls, name):
        demiurge.demiurge_create_cluster(cluster_name=name)
        return cls.demiurge_api_get(name=name)

    @classmethod
    def wait_before_removing_cluster(self):
        try:
            if self.wait_before_remove_cluster_sec == 0:
                response = cf.cf_api_get_apps()
                app_guid = next((app["metadata"]["guid"] for app in response
                                 if app["entity"]["name"] == TAP.kubernetes_broker.value), None)
                assert app_guid is not None, "No such app {}".format(TAP.kubernetes_broker)
                app_env = cf.cf_api_get_app_env(app_guid)
                self.wait_before_remove_cluster_sec = app_env["environment_json"]["WAIT_BEFORE_REMOVE_CLUSTER_SEC"]
            return self.wait_before_remove_cluster_sec
        except KeyError:
            return 0
