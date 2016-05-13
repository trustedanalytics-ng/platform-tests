#
# Copyright (c) 2015-2016 Intel Corporation
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
import json

from ..http_calls import cloud_foundry as cf, application_broker, kubernetes_broker
from ..http_calls.platform import service_catalog
from ..test_names import generate_test_object_name


@functools.total_ordering
class ServiceType(object):

    COMPARABLE_ATTRIBUTES = ["label", "guid", "description", "space_guid"]

    def __init__(self, label, guid, description, space_guid, service_plans, tags=None, display_name=None, image=None):
        self.label = label
        self.guid = guid
        self.description = description
        self.space_guid = space_guid
        self.service_plans = service_plans  # service plan is a dict with keys "guid", and "name"
        self.tags = tags
        self.display_name = display_name
        self.image = image

    def __eq__(self, other):
        return all([getattr(self, ca) == getattr(other, ca) for ca in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    def __hash__(self):
        return hash(tuple([getattr(self, ca) for ca in self.COMPARABLE_ATTRIBUTES]))

    def __repr__(self):
        return "{} (label={}, guid={})".format(self.__class__.__name__, self.label, self.guid)

    @property
    def service_plan_guids(self):
        return [sp["guid"] for sp in self.service_plans]

    @classmethod
    def _from_details(cls, space_guid, details):
        metadata = details["metadata"]
        entity = details["entity"]
        service_plans = entity.get("service_plans")
        if service_plans is not None:  # in cf response there are no service plans, but an url
            service_plans = [{"guid": sp["metadata"]["guid"], "name": sp["entity"]["name"]}
                             for sp in entity["service_plans"]]
        extra = json.loads(entity.get("extra") or "{}")
        return cls(label=entity["label"], guid=metadata["guid"], description=entity["description"],
                   space_guid=space_guid, service_plans=service_plans, tags=entity.get("tags"),
                   display_name=extra.get("displayName"), image=extra.get("imageUrl"))

    @classmethod
    def api_get_list_from_marketplace(cls, space_guid, client=None):
        response = service_catalog.api_get_marketplace_services(space_guid=space_guid, client=client)
        return [cls._from_details(space_guid, data) for data in response]

    @classmethod
    def api_get(cls, space_guid, service_guid, client=None):
        response = service_catalog.api_get_service(service_guid=service_guid, client=client)
        return cls._from_details(space_guid, response)

    @classmethod
    def register_app_in_marketplace(cls, app_name, app_guid, org_guid, space_guid, service_name=None,
                                    service_description=None, image=None, display_name=None, tags=None, client=None):
        service_name = generate_test_object_name(short=True) if service_name is None else service_name
        service_description = generate_test_object_name(short=True) if service_description is None else service_description
        response = service_catalog.api_create_service(service_name, service_description, org_guid, app_name, app_guid,
                                                      image, display_name, tags, client)
        return cls._from_details(space_guid, response)

    def api_get_service_plans(self, client=None):
        """
        Return a list of dicts with "guid" and "name" keys
        retrieved from /rest/services/{service_type_label}/service_plans
        """
        response = service_catalog.api_get_service_plans(self.label, client)
        service_plans = []
        for sp_data in response:
            name = sp_data["entity"]["name"]
            guid = sp_data["metadata"]["guid"]
            service_plans.append({"name": name, "guid": guid})
        self.service_plans = service_plans

    def api_delete(self, client=None):
        service_catalog.api_delete_service(self.guid, client)

    @classmethod
    def cf_api_get_list_from_marketplace_by_space(cls, space_guid):
        response = cf.cf_api_get_space_services(space_guid)
        return [cls._from_details(space_guid, data) for data in response["resources"]]

    @classmethod
    def cf_api_get_list(cls, name=None, get_plans=False):
        response = cf.cf_api_get_services(service_name=name)
        services = []
        for service_info in response:
            service = cls._from_details(space_guid=None, details=service_info)
            if get_plans:
                plans_response = cf.cf_api_get_service_plans(service_guid=service.guid)
                service.service_plans = []
                for plan_info in plans_response["resources"]:
                    service.service_plans.append({"name": plan_info["entity"]["name"],
                                                  "guid": plan_info["metadata"]["guid"]})
            services.append(service)
        return services

    @classmethod
    def app_broker_create_service_in_catalog(cls, service_name, description, app_guid):
        response = application_broker.app_broker_create_service(app_guid, description, service_name)
        service_plans = response.get("plans")
        return cls(label=response["name"], guid=response["id"], description=response["description"],
                   space_guid=response["app"]["entity"]["space_guid"], service_plans=service_plans)

    @classmethod
    def k8s_broker_create_dynamic_service(cls, org_guid, space_guid, service_name=None):
        if service_name is None:
            service_name = generate_test_object_name(short=True)
        kubernetes_broker.k8s_broker_create_service_offering(org_guid=org_guid, space_guid=space_guid,
                                                             service_name=service_name)
        return service_name

    @classmethod
    def k8s_broker_get_catalog(cls):
        response = kubernetes_broker.k8s_broker_get_catalog()
        services = []
        for service_info in response["services"]:
            plans = []
            for plan_info in service_info["plans"]:
                plans.append({"name": plan_info["name"], "guid": plan_info["id"]})
            service = cls(label=service_info["name"], guid=service_info["id"], description=service_info["description"],
                          space_guid=None, service_plans=plans)
            services.append(service)
        return services

    def cf_api_enable_service_access(self, plan=None):
        if plan is None:
            plan = self.service_plans[0]
        cf.cf_api_update_service_access(plan["guid"], enable_service=True)

    def cf_api_disable_service_access(self, plan=None):
        if plan is None:
            plan = self.service_plans[0]
        cf.cf_api_update_service_access(plan["guid"], enable_service=False)
