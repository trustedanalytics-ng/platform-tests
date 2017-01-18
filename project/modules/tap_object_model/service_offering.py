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

import json
import functools

from retry import retry

from fixtures.k8s_templates import template_example
from modules import file_utils
from modules.constants import TapEntityState, ServicePlan as ServicePlanNames
from modules.exceptions import ServiceOfferingCreationFailed
from modules.http_calls.platform import api_service as api
from modules.http_client import HttpClient
from modules.tap_logger import get_logger
from modules.test_names import generate_test_object_name
from ._service_plan import ServicePlan
from ._api_model_superclass import ApiModelSuperclass
from ._tap_object_superclass import TapObjectSuperclass

logger = get_logger(__name__)


@functools.total_ordering
class ServiceOffering(ApiModelSuperclass, TapObjectSuperclass):

    _COMPARABLE_ATTRIBUTES = ["id", "label"]
    TEST_SERVICE_PREFIX = "test_service"

    def __init__(self, *, offering_id: str, label: str, service_plans: list, state: str, tags: list=None,
                 image: str=None, display_name: str=None, client: HttpClient=None):
        # TODO add fields necessary for tests
        super().__init__(object_id=offering_id, client=client)
        self.label = label
        self.service_plans = service_plans
        self.state = state
        self.tags = tags if tags is not None else []
        self.image = image
        self.display_name = display_name

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
        new_offering = cls(offering_id=offering_from_response.id, label=label, service_plans=service_plans,
                           state=offering_from_response.state)
        context.test_objects.append(new_offering)
        assert new_offering == offering_from_response
        return new_offering

    @retry(AssertionError, tries=60, delay=3)
    def ensure_ready(self):
        self._refresh()
        if self.state == TapEntityState.OFFLINE:
            raise ServiceOfferingCreationFailed()
        assert self.state == TapEntityState.READY, "Offering state is {}, expected {}".format(self.state,
                                                                                              TapEntityState.READY)

    def _refresh(self):
        offerings = self.get_list()
        this_offering = next((i for i in offerings if i.id == self.id), None)
        assert this_offering is not None, "Offering {} not found on the list".format(self.label)
        self.state = this_offering.state

    @classmethod
    def create_from_binary(cls, context, *, jar_path, manifest_path, offering_path, client: HttpClient=None):
        if client is None:
            client = cls._get_default_client()
        response = api.create_offering_from_binary(jar_path=jar_path, manifest_path=manifest_path,
                                                   offering_path=offering_path, client=client)
        new_offering = cls._from_response(response, client)
        context.test_objects.append(new_offering)
        return new_offering

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
        response = api.get_offerings(client=client)
        return cls._list_from_response(response, client)

    @retry(AssertionError, tries=10, delay=2)
    def delete(self, client=None):
        api.delete_offering(client=self._get_client(client), offering_id=self.id)

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        # TODO this workaround for inconsistent responses will not be required
        offering_id = response.get("id")
        state = response.get("state")
        label = response.get("name")
        service_plans_json = response.get("plans")
        if service_plans_json is None:
            service_plans_json = response.get("offeringPlans")
        if service_plans_json is None:
            logger.debug("Why service_plans_json is None?")
            logger.debug(response)
            service_plans_json = []
        tags = response.get("tags")
        if type(response["metadata"]) is list:
            metadata = cls._metadata_to_dict(response["metadata"])
            image = metadata.get("imageUrl", None)
            display_name = metadata.get("displayName", None)
        else:
            image = None
            display_name = None
        service_plans = []
        for item in service_plans_json:
            service_plans.append(ServicePlan.from_response(item))
        return cls(offering_id=offering_id, label=label, service_plans=service_plans, image=image, state=state,
                   tags=tags, display_name=display_name, client=client)

    @classmethod
    def _metadata_to_dict(cls, metadata):
        metadata_dict = {}
        if metadata is not None:
            for pair in metadata:
                metadata_dict.update({pair["key"]: pair["value"]})
        return metadata_dict

    @classmethod
    def create_offering_json(cls, name: str=None, description: str=None, metadata: list=None, bindable: bool=True,
                             tags: list=None, plans: list=None, file_name: str=None):
        default_plans = [{
            "name": ServicePlanNames.FREE,
            "description": ServicePlanNames.FREE,
            "cost": ServicePlanNames.FREE
        }]
        offering_dict = {
            "name": name if name is not None else generate_test_object_name(separator="-"),
            "description": description if description is not None else generate_test_object_name(),
            "metadata": metadata if metadata is not None else [],
            "bindable": bindable,
            "tags": tags if tags is not None else [],
            "plans": plans if plans is not None else default_plans
        }
        file_name = file_name if file_name is not None else "offering.json"
        return file_utils.save_text_file(data=json.dumps(offering_dict), file_name=file_name)

    @classmethod
    def create_manifest_json(cls, app_type: str, file_name: str=None):
        manifest_dict = {
            "type": app_type
        }
        file_name = file_name if file_name is not None else "manifest.json"
        return file_utils.save_text_file(data=json.dumps(manifest_dict), file_name=file_name)
