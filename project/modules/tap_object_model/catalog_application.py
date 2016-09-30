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

    def __init__(self, application_id: str, replication=None, instance_id=None, instance_name=None, instance_state=None):
        self.id = application_id
        self.replication = replication
        self.instance_id = instance_id
        self.instance_name = instance_name
        self.instance_state = instance_state

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, template_id, image_id, name=None):
        response = catalog.create_application(name or generate_test_object_name(separator="-"),
                                              template_id, image_id)
        new_application = cls._from_response(response)
        context.catalog.append(new_application)
        return new_application

    @classmethod
    def get(cls, application_id: str):
        response = catalog.get_application(application_id)
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

    @classmethod
    def _from_response(cls, response):
        return cls(application_id=response["id"], replication=response["replication"])

    def update(self, field, value):
        setattr(self, field, value)
        catalog.update_application(self.id, field, value)

    @classmethod
    def create_instance(cls, context, application_id, body, instance_name):
        if body:
            body["name"] = instance_name
        response = catalog.create_application_instance(application_id, body)
        new_instance = cls._from_instance_response(response)
        context.catalog.append(new_instance)
        return new_instance

    @classmethod
    def get_instance(cls, application_id: str, instance_id: str):
        response = catalog.get_application_instance(application_id, instance_id)
        return cls._from_instance_response(response)

    @classmethod
    def get_instances_list(cls, application_id: str):
        response = catalog.get_application_instances(application_id)
        services = []
        for item in response:
            service = cls._from_instance_response(item)
            services.append(service)
        return services

    @classmethod
    def get_all_services_instances_list(cls):
        response = catalog.get_all_applications_instances()
        services = []
        for item in response:
            service = cls._from_instance_response(item)
            services.append(service)
        return services

    def update_instance(self, field, value):
        setattr(self, field, value)
        catalog.update_application_instance(self.id, self.instance_id, field, value)

    def delete_application_instance(self):
        catalog.delete_service_instance(service_id=self.id, instance_id=self.instance_id)

    @classmethod
    def _from_instance_response(cls, response):
        return cls(application_id=response["classId"], instance_id=response["id"], instance_name=response["name"],
                   instance_state=response["state"])
