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
import uuid

from retry import retry

import modules.http_calls.platform.catalog as catalog


@functools.total_ordering
class CatalogInstance(object):

    def __init__(self, instance_id: str, class_id: str, name: str):
        self.id = instance_id
        self.name = name
        self.classId = class_id

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, service_id, body, instance_name):
        if body:
            body["name"] = instance_name
        response = catalog.create_service_instance(service_id, body)
        new_instance = cls._from_response(response)
        context.catalog.append(new_instance)
        return new_instance

    @classmethod
    def get(cls, instance_id: str):
        response = catalog.get_instance(instance_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog.get_instances()
        instances = []
        for item in response:
            instance = cls._from_response(item)
            instances.append(instance)
        return instances

    def delete(self):
        catalog.delete_instance(instance_id=self.id)

    def cleanup(self):
        self.delete()

    @classmethod
    def _from_response(cls, response):
        return cls(instance_id=response["id"], class_id = response["classId"], name=response["name"])

    def update(self, field, value):
        setattr(self, field, value)
        catalog.update_instance(self.id, field, value)