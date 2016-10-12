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

from ._tap_object_superclass import TapObjectSuperclass

class ServicePlan(TapObjectSuperclass):

    _COMPARABLE_ATTRIBUTES = ["id", "name", "description"]

    def __init__(self, plan_id: str, name: str, description: str):
        super().__init__(object_id=plan_id)
        self.name = name
        self.description = description

    def __repr__(self):
        return "{} (name={}, id={})".format(self.__class__.__name__, self.name, self.id)

    def to_dict(self):
        return {"name": self.name, "description": self.description, "cost": "free"}

    @classmethod
    def from_response(cls, response):
        # TODO this workaround for inconsistent responses will not be required
        plan_id = response.get("id")
        if plan_id is None:
            plan_id = response["metadata"]["guid"]
        response = response.get("entity", response)
        return cls(plan_id=plan_id, name=response["name"], description=response["description"])

