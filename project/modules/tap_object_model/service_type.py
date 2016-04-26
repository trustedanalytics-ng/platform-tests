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

from ..http_calls import cloud_foundry as cf, application_broker as broker_client
from ..http_calls.platform import service_catalog


@functools.total_ordering
class ServiceType(object):

    COMPARABLE_ATTRIBUTES = ["label", "guid", "description", "space_guid"]

    def __init__(self, label, guid, description, space_guid, service_plans):
        self.label = label
        self.guid = guid
        self.description = description
        self.space_guid = space_guid
        self.service_plans = service_plans  # service plan is a dict with keys "guid", and "name"

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
        return cls(label=entity["label"], guid=metadata["guid"], description=entity["description"],
                   space_guid=space_guid, service_plans=service_plans)

    @classmethod
    def api_get_list_from_marketplace(cls, space_guid, client=None):
        response = service_catalog.api_get_marketplace_services(space_guid=space_guid, client=client)
        return [cls._from_details(space_guid, data) for data in response]

    @classmethod
    def api_get(cls, space_guid, service_guid, client=None):
        response = service_catalog.api_get_service(service_guid=service_guid, client=client)
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

    @classmethod
    def cf_api_get_list_from_marketplace_by_space(cls, space_guid):
        response = cf.cf_api_get_space_services(space_guid)
        return [cls._from_details(space_guid, data) for data in response["resources"]]

    @classmethod
    def cf_api_get_list(cls):
        response = cf.cf_api_get_services()
        services = []

        for service in response:
            services.append(cls._from_details(space_guid=None, details=service))
        return services

    @classmethod
    def app_broker_create_service_in_catalog(cls, service_name, description, app_guid):
        service = broker_client.app_broker_create_service(app_guid, description, service_name)
        service_plans = service.get("plans")
        return cls(label=service["name"], guid=service["id"], description=service["description"],
                   space_guid=service["app"]["entity"]["space_guid"], service_plans=service_plans)





