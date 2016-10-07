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


from modules.http_calls import kubernetes as kubernetes_api


class KubernetesPod(object):
    RUNNING = "Running"

    def __init__(self, name, state, instance_id_label=None, containers=None):
        self.name = name
        self.state = state
        self.instance_id_label = instance_id_label
        self.containers = containers

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    @classmethod
    def get_list(cls):
        response = kubernetes_api.k8s_get_pods()
        pods = []
        for item in response["items"]:
            pod = cls._from_response(item)
            pods.append(pod)
        return pods

    @classmethod
    def _from_response(cls, response):
        return cls(name=response["metadata"]["name"], state=response["status"]["phase"],
                   instance_id_label=response["metadata"].get("labels", {}).get("instance_id"),
                   containers=response["spec"].get("containers"))
