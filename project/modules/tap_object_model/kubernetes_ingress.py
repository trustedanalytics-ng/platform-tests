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

from modules.http_calls import kubernetes


@functools.total_ordering
class KubernetesIngress(object):

    comparable_attributes = ["name"]

    def __init__(self, name, hosts):
        self.name = name
        self.hosts = hosts

    def __eq__(self, other):
        return all((getattr(self, a) == getattr(other, a) for a in self.comparable_attributes))

    def __lt__(self, other):
        return self.name < other.name

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self.comparable_attributes))

    @classmethod
    def _from_item(cls, item):
        return cls(name=item["metadata"]["name"], hosts=[i["host"] for i in item["spec"]["rules"]])

    @classmethod
    def get_list(cls):
        response = kubernetes.k8s_get_ingresses()
        ingresses = []
        for item in response["items"]:
            ingresses.append(cls._from_item(item))
        return ingresses

    @classmethod
    def get_ingress_by_tap_name(cls, tap_name):
        for ingress in cls.get_list():
            for host in ingress.hosts:
                if host and host.startswith(tap_name):
                    return ingress
        raise AssertionError("Can't find ingress with tap_name: {}".format(tap_name))
