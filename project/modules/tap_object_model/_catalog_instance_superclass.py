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
class CatalogInstanceSuperClass(object):
    """
    Base class for all CatalogInstance* classes.
    """

    _COMPARABLE_ATTRIBUTES = ["id", "name", "type", "class_id", "state"]

    def __init__(self, instance_id: str, name: str, instance_type: str, class_id: str, state: str):
        self.id = instance_id
        self.name = name
        self.type = instance_type
        self.class_id = class_id
        self.state = state

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    @classmethod
    def _from_response(cls, response: dict):
        return cls(instance_id=response["id"], instance_type=response["type"], class_id=response["classId"],
                   state=response["state"])

    @classmethod
    def _list_from_response(cls, response: list) -> list:
        instances = []
        for item in response:
            instance = cls._from_response(item)
            instances.append(instance)
        return instances

    def delete(self):
        return NotImplemented

    def cleanup(self):
        self.delete()
