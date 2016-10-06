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

import modules.http_calls.platform.catalog as catalog_api
from modules.test_names import generate_test_object_name


@functools.total_ordering
class CatalogService(object):
    _COMPARABLE_ATTRIBUTES = ["id", "name", "description", "template_id", "state"]

    def __init__(self, *, service_id, name, description, template_id, state):
        self.id = service_id
        self.name = name
        self.description = description
        self.template_id = template_id
        self.state = state

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (name={}, id={})".format(self.__class__.__name__, self.name, self.id)

    @classmethod
    def _from_response(cls, response):
        return cls(service_id=response["id"], name=response["name"], description=response["description"],
                   template_id=response["templateId"], state=response["state"])

    @classmethod
    def create(cls, context, *, template_id, name=None, bindable=True, plans=None):
        if name is None:
            name = generate_test_object_name().replace("_", "-")
        response = catalog_api.create_service(template_id=template_id, name=name, bindable=bindable, plans=plans)
        new_service = cls._from_response(response)
        context.catalog.append(new_service)
        return new_service

    @classmethod
    def get(cls, *, service_id: str):
        response = catalog_api.get_service(service_id=service_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog_api.get_services()
        services = []
        for item in response:
            service = cls._from_response(item)
            services.append(service)
        return services

    def update(self, *, field_name, value):
        setattr(self, field_name, value)
        catalog_api.update_service(service_id=self.id, field_name=field_name, value=value)

    def delete(self):
        catalog_api.delete_service(service_id=self.id)

    def cleanup(self):
        self.delete()


    # @classmethod
    # def create_instance(cls, context, service_id, body, instance_name):
    #     if body:
    #         body["name"] = instance_name
    #     response = catalog.create_service_instance(service_id, body)
    #     new_instance = cls._from_instance_response(response)
    #     context.catalog.append(new_instance)
    #     return new_instance
    #
    # @classmethod
    # def get_instance(cls, service_id: str, instance_id: str):
    #     response = catalog.get_service_instance(service_id, instance_id)
    #     return cls._from_instance_response(response)
    #
    # @classmethod
    # def get_instances_list(cls, service_id: str):
    #     response = catalog.get_service_instances(service_id)
    #     services = []
    #     for item in response:
    #         service = cls._from_instance_response(item)
    #         services.append(service)
    #     return services
    #
    # @classmethod
    # def get_all_services_instances_list(cls):
    #     response = catalog.get_all_services_instances()
    #     services = []
    #     for item in response:
    #         service = cls._from_instance_response(item)
    #         services.append(service)
    #     return services
    #
    # def update_instance(self, field, value):
    #     setattr(self, field, value)
    #     catalog.update_service_instance(self.id, self.instance_id, field, value)
    #
    # def delete_instance(self):
    #     catalog.delete_service_instance(service_id=self.id, instance_id=self.instance_id)
    #
    # @classmethod
    # def _from_instance_response(cls, response):
    #     return cls(service_id=response["classId"], instance_id=response["id"], instance_name=response["name"])
