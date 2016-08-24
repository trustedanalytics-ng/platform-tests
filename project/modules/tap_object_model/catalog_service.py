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
import fixtures.k8s_templates.catalog_service_example as service_body
import modules.http_calls.platform.catalog as catalog


@functools.total_ordering
class CatalogService(object):

    def __init__(self, service_id, instance_id=None, instance_name=None):
        self.id = service_id
        self.instance_id = instance_id
        self.instance_name = instance_name

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, template_id):
        body = service_body.ng_catalog_service_correct_body
        body["name"] += uuid.uuid4().hex
        body["templateId"] = template_id
        response = catalog.create_service(body)
        new_service = cls._from_response(response)
        context.catalog.append(new_service)
        return new_service

    @classmethod
    def get(cls, service_id: str):
        response = catalog.get_service(service_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog.get_services()
        services = []
        for item in response:
            service = cls._from_response(item)
            services.append(service)
        return services

    def delete(self):
        catalog.delete_service(service_id=self.id)

    def cleanup(self):
        self.delete()

    @classmethod
    def _from_response(cls, response):
        return cls(service_id=response["id"])

    def update(self, field, value):
        setattr(self, field, value)
        catalog.update_service(self.id, field, value)

    @classmethod
    def create_instance(cls, context, service_id, body, instance_name):
        if body:
            body["name"] = instance_name
        response = catalog.create_service_instance(service_id, body)
        new_instance = cls._from_instance_response(response)
        context.catalog.append(new_instance)
        return new_instance

    @classmethod
    def get_instance(cls, service_id: str, instance_id: str):
        response = catalog.get_service_instance(service_id, instance_id)
        return cls._from_instance_response(response)

    @classmethod
    def get_instances_list(cls, service_id: str):
        response = catalog.get_service_instances(service_id)
        services = []
        for item in response:
            service = cls._from_instance_response(item)
            services.append(service)
        return services

    @classmethod
    def get_all_services_instances_list(cls):
        response = catalog.get_all_services_instances()
        services = []
        for item in response:
            service = cls._from_instance_response(item)
            services.append(service)
        return services

    def update_instance(self, field, value):
        setattr(self, field, value)
        catalog.update_service_instance(self.id, self.instance_id, field, value)

    def delete_instance(self):
        catalog.delete_service_instance(service_id=self.id, instance_id=self.instance_id)

    @classmethod
    def _from_instance_response(cls, response):
        return cls(service_id=response["classId"], instance_id=response["id"], instance_name=response["name"])
