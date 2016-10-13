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

from fixtures.k8s_templates import template_example
from modules.http_calls.platform import api_service as api
from modules.http_client import HttpClient
from modules.test_names import generate_test_object_name
from ._service_plan import ServicePlan
from ._api_model_superclass import ApiModelSuperclass
from ._tap_object_superclass import TapObjectSuperclass


@functools.total_ordering
class ServiceOffering(ApiModelSuperclass, TapObjectSuperclass):

    _COMPARABLE_ATTRIBUTES = ["guid", "label", "service_plans"]
    TEST_SERVICE_PREFIX = "test_service"

    def __init__(self, *, offering_id: str, label: str, service_plans: list, client: HttpClient=None):
        # TODO add fields necessary for tests
        super().__init__(object_id=offering_id, client=client)
        self.label = label
        self.service_plans = service_plans

    def __repr__(self):
        return "{} (label={}, guid={})".format(self.__class__.__name__, self.label, self.id)

    @classmethod
    def create(cls, context, *, label: str=None, service_plans: list=None, client: HttpClient=None,
               template_body=template_example.etcd_template["body"]):
        # TODO For now, it is assumed that tests create only one offering at a time
        # TODO if there are cases for creating multiple offerings, refactor this method, as well as api.create_offering
        if label is None:
            label = generate_test_object_name(short=True, separator="")
        if service_plans is None:
            service_plans = [ServicePlan(plan_id=None, name="test", description="test")]
        assert all([isinstance(sp, ServicePlan) for sp in service_plans])
        if client is None:
            client = cls._get_default_client()

        response = api.create_offering(client=client, template_body=template_body, service_name=label,
                                       description="Test offering", bindable=True, tags=["test"],
                                       plans=[sp.to_dict() for sp in service_plans])

        assert len(response) == 1, "Incorrect number of offerings returned: {}, should be: 1".format(len(response))

        offering_from_response = cls._from_response(response[0], client)
        new_offering = cls(guid=offering_from_response.id, label=label, plans=service_plans)
        context.append(new_offering)
        assert new_offering == offering_from_response
        return new_offering

    @classmethod
    def create_from_binary(cls, context, *, path):
        # TODO will call POST /offerings/binary in api-service
        raise NotImplemented

    @classmethod
    def get(cls, *, offering_id, client: HttpClient=None):
        if client is None:
            client = cls._get_default_client()
        response = api.get_offering(client=client, offering_id=offering_id)
        return cls._from_response(response, client)

    @classmethod
    def get_list(cls, *, client: HttpClient=None):
        if client is None:
            client = cls._get_default_client()
        response = api.get_catalog(client=client)
        return cls._list_from_response(response, client)

    def delete(self, client=None):
        api.delete_offering(client=self._get_client(client), offering_id=self.id)

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        # TODO this workaround for inconsistent responses will not be required
        offering_id = response.get("id")
        if offering_id is None:
            offering_id = response["metadata"]["guid"]
        label = response.get("name")
        if label is None:
            label = response["entity"]["label"]
        service_plans_json = response.get("plans")
        if service_plans_json is None:
            service_plans_json = response["entity"]["service_plans"]
        service_plans = []
        for item in service_plans_json:
            service_plans.append(ServicePlan.from_response(item))
        return cls(offering_id=offering_id, label=label, service_plans=service_plans, client=client)
