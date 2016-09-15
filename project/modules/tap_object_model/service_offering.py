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

import config
from fixtures.k8s_templates import template_example
from modules.http_calls.platform import api_service as api
from modules.http_client import HttpClientConfiguration, HttpClientType, HttpClientFactory
from modules.test_names import generate_test_object_name
from .service_plan import ServicePlan


@functools.total_ordering
class ServiceOffering(object):
    """TODO merge with ServiceType class into a single ServiceOffering class"""

    COMPARABLE_ATTRIBUTES = ["guid", "label", "service_plans"]

    def __init__(self, guid: str, label: str, service_plans: list):
        # TODO add fields necessary for tests
        self.label = label
        self.guid = guid
        self.service_plans = service_plans

    def __repr__(self):
        return "{} (label={}, guid={})".format(self.__class__.__name__, self.label, self.guid)

    def __lt__(self, other):
        return self.guid < other.guid

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self.COMPARABLE_ATTRIBUTES)

    @classmethod
    def create(cls, context, label: str=None, service_plans: list=None,
               template_body=template_example.etcd_template["body"]):
        if label is None:
            label = generate_test_object_name(short=True, separator="")
        if service_plans is None:
            service_plans = [ServicePlan(guid=None, name="test", description="test")]
        assert all([isinstance(sp, ServicePlan) for sp in service_plans])
        response = api.create_offering(
            client=cls._get_client(),
            template_body=template_body,
            service_name=label,
            description="Test offering",
            bindable=True,
            tags=["test"],
            plans=[sp.to_dict() for sp in service_plans]
        )
        # TODO if there are cases for creating multiple offerings, refactor this method, as well as api.create_offering
        # For now, it is assumed that tests create only one offering at a time
        assert len(response) == 1, "Incorrect number of offerings returned: {}, should be: 1".format(len(response))
        offering_from_response = cls._from_response(response[0])
        new_offering = cls(guid=offering_from_response.guid, label=label, plans=service_plans)
        context.append(new_offering)
        assert new_offering == offering_from_response
        return new_offering

    @classmethod
    def get(cls, offering_id):
        response = api.get_offering(client=cls._get_client(), offering_id=offering_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = api.get_catalog(client=cls._get_client())
        offerings = []
        for item in response:
            offerings.append(cls._from_response(item))
        return offerings

    def delete(self):
        api.delete_offering(client=self._get_client(), offering_id=self.guid)

    def cleanup(self):
        self.delete()

    @classmethod
    def _from_response(cls, response):
        # workaround for inconsistent responses
        guid = response.get("id")
        if guid is None:
            guid = response["metadata"]["guid"]
        label = response.get("name")
        if label is None:
            label = response["entity"]["label"]
        service_plans_json = response.get("plans")
        if service_plans_json is None:
            service_plans_json = response["entity"]["service_plans"]
        service_plans = []
        for item in service_plans_json:
            service_plans.append(ServicePlan.from_response(item))
        return cls(guid=guid, label=label, service_plans=service_plans)

    @classmethod
    def _get_client(cls):
        configuration = HttpClientConfiguration(client_type=HttpClientType.K8S_SERVICE, url=config.api_url_full,
                                                username=config.admin_username, password=config.admin_password)
        return HttpClientFactory.get(configuration)
