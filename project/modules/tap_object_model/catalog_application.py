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

import modules.http_calls.platform.catalog as catalog
from modules.test_names import generate_test_object_name


@functools.total_ordering
class CatalogApplication(object):
    _COMPARABLE_ATTRIBUTES = ["id", "name", "description", "replication", "image_id", "template_id"]

    def __init__(self, *, application_id: str, name: str, description: str, replication: int, image_id: str,
                 template_id: str):
        self.id = application_id
        self.name = name
        self.description = description
        self.replication = replication
        self.image_id = image_id
        self.template_id = template_id

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (name={}, id={})".format(self.__class__.__name__, self.name, self.id)

    @classmethod
    def _from_response(cls, response):
        return cls(application_id=response["id"], name=response["name"], description=response["description"],
                   replication=response["replication"], image_id=response["imageId"],
                   template_id=response["templateId"])

    @classmethod
    def create(cls, context, *, template_id, image_id, name=None, replication=1, description=None):
        if name is None:
            name = generate_test_object_name(separator="-")
        response = catalog.create_application(name=name, template_id=template_id, image_id=image_id,
                                              replication=replication, description=description)
        new_application = cls._from_response(response)
        context.test_objects.append(new_application)
        return new_application

    @classmethod
    def get(cls, *, application_id: str):
        response = catalog.get_application(application_id=application_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog.get_applications()
        applications = []
        for item in response:
            application = cls._from_response(item)
            applications.append(application)
        return applications

    def delete(self):
        catalog.delete_application(application_id=self.id)

    def cleanup(self):
        self.delete()

    def update(self, *, field_name, value, prev_value=None, username=None):
        setattr(self, field_name, value)
        catalog.update_application(application_id=self.id, field_name=field_name, value=value, prev_value=prev_value,
                                   username=username)
