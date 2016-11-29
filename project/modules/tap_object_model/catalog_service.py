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
from ._service_plan import ServicePlan


@functools.total_ordering
class CatalogService(object):
    _COMPARABLE_ATTRIBUTES = ["id", "name", "description", "template_id", "state"]

    def __init__(self, *, service_id, name, description, template_id, state, plans: list):
        self.id = service_id
        self.name = name
        self.description = description
        self.template_id = template_id
        self.state = state
        self.plans = [] if plans is None else plans

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (name={}, id={})".format(self.__class__.__name__, self.name, self.id)

    @classmethod
    def _from_response(cls, response):
        service_plans = []
        if response["plans"] is not None:
            for item in response["plans"]:
                service_plans.append(ServicePlan.from_response(item))
        return cls(service_id=response["id"], name=response["name"], description=response["description"],
                   template_id=response["templateId"], state=response["state"], plans=service_plans)

    @classmethod
    def create(cls, context, *, template_id, name=None, description=None, bindable=True, state=None, plans=None):
        if name is None:
            name = generate_test_object_name().replace("_", "-")
        if plans is None:
            plans = [ServicePlan(plan_id=None, name="test", description="test")]
        response = catalog_api.create_service(template_id=template_id, name=name, description=description,
                                              bindable=bindable, state=state, plans=[sp.to_dict() for sp in plans])
        new_service = cls._from_response(response)
        context.test_objects.append(new_service)
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

    def create_plan(self, body):
        new_plan = ServicePlan.create(service_id=self.id, body=body)
        self.plans.append(new_plan)
        return new_plan

    def update(self, *, field_name, value, prev_value=None, username=None):
        setattr(self, field_name, value)
        catalog_api.update_service(service_id=self.id, field_name=field_name, value=value, prev_value=prev_value,
                                   username=username)

    def delete(self):
        for plan in self.plans:
            ServicePlan.delete_plan(service_id=self.id, plan_id=plan.id)
        catalog_api.delete_service(service_id=self.id)

    def cleanup(self):
        self.delete()
