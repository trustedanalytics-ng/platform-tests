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

import functools

from retry import retry

from modules.http_calls import kubernetes_broker


@functools.total_ordering
class KubernetesInstance(object):

    comparable_attributes = ["guid", "org_guid", "space_guid", "is_visible"]

    def __init__(self, guid, plan_guid, org_guid, space_guid, uris=None, is_visible=None):
        self.guid = guid
        self.plan_guid = plan_guid
        self.org_guid = org_guid
        self.space_guid = space_guid
        self.uris = uris
        self.is_visible = is_visible

    def __eq__(self, other):
        return all((getattr(self, a) == getattr(other, a) for a in self.comparable_attributes))

    def __lt__(self, other):
        return self.guid < other.guid

    def __repr__(self):
        return "{} (guid={})".format(self.__class__.__name__, self.guid)

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self.comparable_attributes))

    @classmethod
    def from_service_instance(cls, guid, plan_guid, space_guid, org_guid):
        return cls(guid=guid, plan_guid=plan_guid, space_guid=space_guid, org_guid=org_guid)

    @classmethod
    def _from_nodes(cls, nodes):
        is_visible = nodes[0]["tapPublic"]
        assert all([node["tapPublic"] == is_visible for node in nodes])
        org_guid = nodes[0]["org"]
        assert all([node["org"] == org_guid for node in nodes])
        space_guid = nodes[0]["space"]
        assert all([node["space"] == space_guid for node in nodes])
        guid = nodes[0]["serviceId"]
        assert all([node["serviceId"] == guid for node in nodes])
        uris = []
        for node in nodes:
            uris.extend(node.get("uris", []))
        return cls(guid=guid, plan_guid=None, org_guid=org_guid, space_guid=space_guid, uris=uris, is_visible=is_visible)

    def get_info(self):
        response = kubernetes_broker.k8s_broker_get_instance(org_guid=self.org_guid, space_guid=self.space_guid,
                                                             service_id=self.guid)
        k8s_instance = self._from_nodes(response)
        self.is_visible = k8s_instance.is_visible
        self.uris = k8s_instance.uris

    @classmethod
    def get_list(cls, org_guid, space_guid):
        response = kubernetes_broker.k8s_broker_get_instance_list(org_guid=org_guid, space_guid=space_guid)
        instance_data = {}
        for node in response:
            instance_guid = node["serviceId"]
            instance_data[instance_guid] = instance_data.get(instance_guid, []) + [node]
        instances = []
        for _, node_info in instance_data.items():
            instances.append(cls._from_nodes(node_info))
        return instances

    @retry(AssertionError, tries=180, delay=5)
    def ensure_running_in_cluster(self):
        response = kubernetes_broker.k8s_broker_get_service_status(org_guid=self.org_guid, service_id=self.guid)
        this_instance = next((i for i in response if i["ServiceId"] == self.guid), None)
        assert this_instance is not None
        assert this_instance["Status"] == "Running"

    def change_visibility(self, visibility=True):
        assert self.plan_guid is not None, "Plan guid is not set for KubernetesInstance object"
        kubernetes_broker.k8s_broker_change_instance_visibility(org_guid=self.org_guid, space_guid=self.space_guid,
                                                                plan_id=self.plan_guid, service_id=self.guid,
                                                                visibility=visibility)

    def delete(self):
        kubernetes_broker.k8s_broker_delete_instance(instance_guid=self.guid)
