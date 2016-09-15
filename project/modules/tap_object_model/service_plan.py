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


@functools.total_ordering
class ServicePlan(object):

    COMPARABLE_ATTRIBUTES = ["guid", "name", "description"]

    def __init__(self, guid: str, name: str, description: str):
        self.guid = guid
        self.name = name
        self.description = description

    def __repr__(self):
        return "{} (name={}, guid={})".format(self.__class__.__name__, self.name, self.guid)

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return all((getattr(self, a) == getattr(other, a) for a in self.COMPARABLE_ATTRIBUTES))

    def to_dict(self):
        return {"name": self.name, "description": self.description, "cost": "free"}

    @classmethod
    def from_response(cls, response):
        # workarounds for inconsistent response objects
        guid = response.get("id")
        if guid is None:
            guid = response["metadata"]["guid"]
        response = response.get("entity", response)
        return cls(guid=guid, name=response["name"], description=response["description"])

