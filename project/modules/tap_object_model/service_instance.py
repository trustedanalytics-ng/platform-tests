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
import uuid

from retry import retry

from ..constants import ServiceLabels
from ..exceptions import UnexpectedResponseError
from ..http_calls import cloud_foundry as cf, application_broker as app,kubernetes_broker as k8s
from ..http_calls.platform import app_launcher_helper as app_launcher, service_catalog, service_exposer
from ..test_names import get_test_name
from . import ServiceKey


@functools.total_ordering
class ServiceInstance(object):
    COMPARABLE_ATTRS = ["guid", "name", "space_guid", "service_label"]

    def __init__(self, guid, name, space_guid, service_label, bound_apps=None, credentials=None):
        self.guid = guid
        self.name = name
        self.space_guid = space_guid
        self.service_label = service_label
        self.bound_apps = bound_apps or []
        self.credentials = credentials

    def __eq__(self, other):
        return all((getattr(self, a) == getattr(other, a) for a in self.COMPARABLE_ATTRS))

    def __lt__(self, other):
        return self.guid < other.guid

    def __repr__(self):
        return "{} (name={}, guid={})".format(self.__class__.__name__, self.name, self.guid)

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self.COMPARABLE_ATTRS))

    @classmethod
    @retry(AssertionError, tries=100, delay=3)
    def _get_instance_with_retry(cls, instance_name, space_guid, service_label):
        """Wait for created instance and return it"""
        instance_list = cls.api_get_list(space_guid)
        instance = next((i for i in instance_list if i.name == instance_name), None)
        if instance is None:
            raise AssertionError("Instance {} was not created".format(service_label))
        return instance

    # ----------------------------------------- Platform API ----------------------------------------- #

    @classmethod
    def api_create(cls, org_guid, space_guid, service_label, name=None, service_plan_name=None,
                   service_plan_guid=None, params=None, client=None):
        """
        Service instance can be either created passing:
        - service_plan_guid - one api call is used, or
        - service_label and service_plan_name - an additional call is made to retrieve service_plan_guid
        """
        name = get_test_name() if name is None else name
        if all([x is None for x in (service_label, service_plan_name, service_plan_guid)]):
            raise ValueError("service_plan_guid, or service_label and service_plan_name have to be supplied")
        if service_plan_guid is None:
            # retrieve plan guid based on service name and plan name
            response = service_catalog.api_get_service_plans(service_type_label=service_label, client=client)
            service_plan_data = next((item for item in response if item["entity"]["name"] == service_plan_name), None)
            if service_plan_data is None:
                raise ValueError("No such plan {} for service {}".format(service_plan_name, service_label))
            service_plan_guid = service_plan_data["metadata"]["guid"]
        try:
            response = service_catalog.api_create_service_instance(name=name, service_plan_guid=service_plan_guid,
                                                                   org_guid=org_guid, space_guid=space_guid,
                                                                   params=params, client=client)
            return cls(guid=response["metadata"]["guid"], name=name, space_guid=space_guid, service_label=service_label)
        except UnexpectedResponseError as e:
            if e.status == 504 and "Gateway Timeout" in e.error_message:
                return cls._get_instance_with_retry(name, space_guid, service_label)
            raise

    @classmethod
    def api_get_list(cls, space_guid=None, service_type_guid=None, client=None):
        instances = []
        response = service_catalog.api_get_service_instances(space_guid=space_guid, service_guid=service_type_guid,
                                                             client=client)
        for data in response:
            bound_apps = [{"app_guid": binding_data["guid"], "app_name": binding_data["name"]}
                          for binding_data in data["bound_apps"]]
            service_label = data["service_plan"]["service"]["label"] if data.get("service_plan") is not None else None
            instance = cls(guid=data["guid"], name=data["name"], space_guid=space_guid, service_label=service_label,
                           bound_apps=bound_apps)
            instances.append(instance)
        return instances

    @classmethod
    def api_get_keys(cls, space_guid, client=None):
        """Return a dict mapping instances to their keys, retrieved from /rest/service_instances/summary."""
        keys = {}
        response = service_catalog.api_get_service_instances_summary(space_guid=space_guid, service_keys=True,
                                                                     client=client)
        for service_data in response:
            for instance_data in service_data.get("instances", []):
                instance = cls(guid=instance_data["guid"], name=instance_data["name"], space_guid=space_guid,
                               service_label=service_data["label"])
                service_keys = []
                for key_data in instance_data["service_keys"]:
                    service_keys.append(ServiceKey(guid=key_data["guid"], name=key_data["name"],
                                                   credentials=key_data["credentials"],
                                                   service_instance_guid=key_data["service_instance_guid"]))
                keys[instance] = service_keys
        return keys

    def api_get_credentials(self, client=None):
        """Return hostname, login, password from /rest/tools/service_instances"""
        response = service_exposer.api_tools_service_instances(service_label=self.service_label,
                                                               space_guid=self.space_guid, client=client)
        return {
            "hostname": response[self.name]["hostname"],
            "login": response[self.name]["login"],
            "password": response[self.name]["password"]
        }

    def api_delete(self, client=None):
        service_catalog.api_delete_service_instance(self.guid, client=client)

    @classmethod
    def api_get_data_science_service_instances(cls, space_guid, org_guid, service_label):
        return service_exposer.api_tools_service_instances(service_label, space_guid, org_guid)

    # ----------------------------------------- CF API ----------------------------------------- #

    @classmethod
    def cf_api_create(cls, space_guid, service_label, name=None, service_plan_name=None, service_plan_guid=None):
        """
        Service instance can be either created passing:
        - service_plan_guid - one api call is used, or
        - service_label and service_plan_name - 2 additional calls are made to retrieve service_plan_guid
        """
        name = get_test_name() if name is None else name
        if all([x is None for x in (service_label, service_plan_name, service_plan_guid)]):
            raise ValueError("service_plan_guid, or service_label and service_plan_name have to be supplied")
        if service_plan_guid is None:
            # retrieve plan guid based on service name and plan name
            response = cf.cf_api_get_space_services(space_guid=space_guid, label=service_label)
            service_guid = response["resources"][0]["metadata"]["guid"]
            response = cf.cf_api_get_service_plans(service_guid)
            sp_data = next((d for d in response["resources"] if d["entity"]["name"] == service_plan_name), None)
            if sp_data is None:
                raise ValueError("No such plan {} for service {}".format(service_plan_name, service_label))
        response = cf.cf_api_create_service_instance(instance_name=name, space_guid=space_guid,
                                                     service_plan_guid=service_plan_guid)
        return cls(guid=response["metadata"]["guid"], service_label=service_label, name=name, space_guid=space_guid)

    @classmethod
    def cf_api_get_list(cls):
        si_data = cf.cf_api_get_service_instances()
        services = []
        for data in si_data:
            services.append(cls(guid=data["metadata"]["guid"], name=data["entity"]["name"], service_label=None,
                            space_guid=data["entity"]["space_guid"]))
        return services

    @classmethod
    def from_cf_api_space_summary_response(cls, response: dict, space_guid: str) -> list:
        service_instances = []
        for instance_data in response["services"]:
            try:
                service_label = instance_data["service_plan"]["service"]["label"]
            except KeyError:
                service_label = None
            service_instance = cls(guid=instance_data["guid"], name=instance_data["name"], space_guid=space_guid,
                                   service_label=service_label)
            service_instances.append(service_instance)
        return service_instances


    # ----------------------------------------- APPLICATION BROKER API ----------------------------------------- #

    @classmethod
    def app_broker_create_instance(cls, organization_guid, plan_id, service_id, space_guid):
        instance_name = get_test_name()
        instance_guid = uuid.uuid4()
        app.app_broker_new_service_instance(instance_guid, organization_guid, plan_id, service_id, space_guid,
                                                      instance_name)
        return cls(guid=instance_guid, name=instance_name, service_label=None, space_guid=space_guid)


class AtkInstance(ServiceInstance):
    started_status = "STARTED"

    def __init__(self, guid, name, space_guid, org_guid=None, scoring_engine=None, state=None, creator_guid=None,
                 creator_name=None):
        super().__init__(guid, name, space_guid, ServiceLabels.ATK)
        self.state = state.upper() if state is not None else state
        self.scoring_engine = scoring_engine
        self.org_guid = org_guid
        self.creator_guid = creator_guid
        self.creator_name = creator_name

    @classmethod
    def api_get_list_from_data_science_atk(cls, org_guid, client=None):
        response = app_launcher.api_get_atk_instances(org_guid, client=client)
        atk_instances = []
        if response["instances"] is not None:
            for data in response["instances"]:
                instance = cls(guid=data["service_guid"], name=data["name"], space_guid=None, org_guid=org_guid,
                               scoring_engine=data["scoring_engine"], state=data["state"],
                               creator_guid=data["metadata"].get("creator_guid"),
                               creator_name=data["metadata"].get("creator_name"))
                atk_instances.append(instance)
        return atk_instances

