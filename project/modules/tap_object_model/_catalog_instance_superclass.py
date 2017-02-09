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

from modules.constants import TapEntityState
from modules.exceptions import ServiceInstanceCreationFailed


@functools.total_ordering
class CatalogInstanceSuperClass(object):
    """
    Base class for all CatalogInstance* classes.
    """

    _COMPARABLE_ATTRIBUTES = ["id", "name", "type", "class_id"]

    def __init__(self, instance_id: str, name: str, instance_type: str, class_id: str, state: str,
                 bound_instance_ids: list):
        self.id = instance_id
        self.name = name
        self.type = instance_type
        self.class_id = class_id
        self.state = state
        self.bound_instance_ids = bound_instance_ids
        self._is_deleted = False

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (name={}, id={}, type={}, class_id={}, state={})".format(
                self.__class__.__name__, self.name, self.id, self.type,
                self.class_id, self.state)

    @classmethod
    def _from_response(cls, response: dict):
        bindings = response.get("bindings")
        if bindings is None:
            bound_instance_ids = []
        else:
            bound_instance_ids = [i["id"] for i in bindings]
        return cls(instance_id=response["id"], name=response["name"], instance_type=response["type"],
                   class_id=response["classId"], state=response["state"], bound_instance_ids=bound_instance_ids)

    @classmethod
    def _list_from_response(cls, response: list) -> list:
        instances = []
        for item in response:
            instance = cls._from_response(item)
            instances.append(instance)
        return instances

    @classmethod
    def get(cls, *, instance_id):
        return NotImplemented

    def update(self, *, field_name, value):
        return NotImplemented

    def delete(self):
        self.update(field_name="state", value=TapEntityState.DESTROY_REQ)

    def stop(self):
        self.update(field_name="state", value=TapEntityState.STOP_REQ)
        self.ensure_in_state(expected_state=TapEntityState.STOPPED)

    def destroy(self):
        self.update(field_name="state", value=TapEntityState.DESTROY_REQ)

    def cleanup(self):
        if self.state == TapEntityState.RUNNING:
            self.stop()
        self.delete()

    @retry(AssertionError, tries=60, delay=5)
    def ensure_in_state(self, *, expected_state):
        instance = self.get(instance_id=self.id)
        self.state = instance.state
        if expected_state != TapEntityState.FAILURE and self.state == TapEntityState.FAILURE:
            raise ServiceInstanceCreationFailed("{} is in state {}".format(self, self.state))
        assert self.state == expected_state, "{} state is {}, expected {}".format(self, self.state, expected_state)

    def _set_deleted(self, is_deleted):
        self._is_deleted = bool(is_deleted)