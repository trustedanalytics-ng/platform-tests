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
import requests
from retry import retry
from modules.constants import ApiServiceHttpStatus
from modules import test_names
from modules.constants import TapEntityState
from modules.http_client import HttpClient
from modules.exceptions import ServiceInstanceCreationFailed
from modules.exceptions import UnexpectedResponseError
import modules.http_calls.platform.api_service as api
from modules.test_names import generate_test_object_name
from ._api_model_superclass import ApiModelSuperclass
from ._tap_object_superclass import TapObjectSuperclass


class ServiceInstance(ApiModelSuperclass, TapObjectSuperclass):
    """
    ServiceInstance represents a service instance on TAP.
    The class uses 'console' or 'api-service' REST APIs.
    """

    _COMPARABLE_ATTRIBUTES = ["id", "name", "plan_id", "state"]
    PLAN_ID_METADATA_KEY = "PLAN_ID"
    URLS_METADATA_KEY = "urls"

    def __init__(self, *, service_id: str, name: str, offering_id: str, plan_id: str, bindings: list, state: str,
                 offering_label: str=None, url: str=None, client: HttpClient=None):
        super().__init__(object_id=service_id, client=client)
        self.name = name
        self.offering_id = offering_id
        self.offering_label = offering_label
        self.plan_id = plan_id
        self.state = state
        self.bindings = [] if bindings is None else bindings
        self.url = url
        self._is_deleted = False

    def __repr__(self):
        return "{} (name={}, id={}, offering={})".format(self.__class__.__name__, self.name, self.id, self.offering_label)

    @classmethod
    def create(cls, context, *, offering_id: str, plan_id: str, name: str=None,
               params: dict=None, client: HttpClient=None):
        if name is None:
            name = generate_test_object_name(separator="")
        if client is None:
            client = cls._get_default_client()
        response = api.create_service(name=name, plan_id=plan_id, params=params, offering_id=offering_id, client=client)
        instance = cls._from_response(response, client)
        context.test_objects.append(instance)
        return instance

    @classmethod
    def create_with_name(cls, context, *, offering_label: str, plan_name: str, name: str=None, params: dict=None,
                         client: HttpClient=None):
        """
        Create service instance using offering label and plan name.
        First, make call to retrieve offering id and plan id.
        """
        if name is None:
            name = test_names.generate_test_object_name(separator="")
        if client is None:
            client = cls._get_default_client()
        offering_id, plan_id = cls._get_offering_id_and_plan_id_by_names(offering_label=offering_label,
                                                                         plan_name=plan_name, client=client)
        return cls.create(context, offering_id=offering_id, plan_id=plan_id, name=name, params=params, client=client)

    @classmethod
    def get(cls, *, service_id: str, client: HttpClient=None):
        if client is None:
            client = cls._get_default_client()
        response = api.get_service(client=client, service_id=service_id)
        return cls._from_response(response, client)

    @classmethod
    def get_by_name(cls, name: str, client: HttpClient=None):
        if client is None:
            client = cls._get_default_client()
        for service in api.get_services(client=client, name=name):
            if service['name'] == name:
                return cls._from_response(service, client)

    @classmethod
    def get_list(cls, *, name: str=None, offering_id: str=None, plan_name: str=None, limit: int=None, skip: int=None,
                 client: HttpClient=None) -> list:
        if client is None:
            client = cls._get_default_client()
        response = api.get_services(name=name, offering_id=offering_id, plan_name=plan_name, limit=limit, skip=skip,
                                    client=client)
        return cls._list_from_response(response, client)

    @property
    def is_stopped(self) -> bool:
        """Returns True if service is stopped."""
        return self.state.upper() == TapEntityState.STOPPED

    @property
    def is_running(self) -> bool:
        """Returns True if any of the service instances are running."""
        return self.state == TapEntityState.RUNNING

    @retry(AssertionError, tries=60, delay=5)
    def ensure_running(self, client: HttpClient=None):
        self._refresh(client=client)
        if self.state == TapEntityState.FAILURE:
            raise ServiceInstanceCreationFailed()
        assert self.state == TapEntityState.RUNNING, "Instance state is {}, expected {}".format(self.state,
                                                                                                TapEntityState.RUNNING)

    @retry(AssertionError, tries=60, delay=5)
    def ensure_stopped(self, client: HttpClient=None):
        """Waits for the service instance state to change to STOPPED. If somehow
        the service instance state is FAILUR, it won't be checked and function
        quits.

        Args:
            client: HttpClient to use

        Raises:
            AssertionError if the service state doesn't change to STOPPED
            ServiceInstanceCreationFailed if service state changes to FAILURE
        """
        self._refresh(client=client)
        if self.state == TapEntityState.FAILURE:
            raise ServiceInstanceCreationFailed()
        assert self.state == TapEntityState.STOPPED, \
               "Instance state is {}, expected {}".format(self.state, TapEntityState.STOPPED)

    @retry(AssertionError, tries=60, delay=5)
    def ensure_deleted(self):
        instances = self.get_list()
        this_instance = next((i for i in instances if i.id == self.id), None)
        assert this_instance is None, "Instance is is still on the list with status {}".format(this_instance.state)

    def start(self, client: HttpClient=None):
        """ Sends the start command to service instance

        Args:
            client: HttpClient to use
        """
        api.start_service(srv_id=self.id, client=self._get_client(client))

    def stop(self, client: HttpClient=None):
        """ Sends the stop command to service instance

        Args:
            client: HttpClient to use
        """
        api.stop_service(srv_id=self.id, client=self._get_client(client))

    def restart(self, client: HttpClient=None):
        """Sends the restart command to service instance

        Args:
            client: HttpClient to use
        """
        api.restart_service(srv_id=self.id, client=self._get_client(client))

    def bind(self, application_id_to_bound: str=None, service_id_to_bound: str=None, client: HttpClient=None):
        api.bind_service(client=self._get_client(client), service_id=self.id,
                         application_id_to_bound=application_id_to_bound, service_id_to_bound=service_id_to_bound)

    def unbind_app(self, *, application_id: str, client: HttpClient=None):
        return api.unbind_app_from_service(client=self._get_client(client), service_id=self.id,
                                           application_id_to_unbound=application_id)

    def get_bindings(self, client: HttpClient=None):
        return api.get_service_bindings(client=self._get_client(client), service_id=self.id)

    @retry(AssertionError, tries=10, delay=2)
    def ensure_unbound(self, application_id, client: HttpClient = None):
        bindings = self.get_bindings(client=client)
        if bindings is not None:
            ids = next((e["entity"]["app_guid"] for e in bindings), None)
            assert application_id not in ids
        else:
            assert bindings is None

    @retry(AssertionError, tries=30, delay=2)
    def ensure_bound(self, application_id, client: HttpClient = None):
        bindings = self.get_bindings(client=client)
        assert bindings is not None
        ids = next((e["entity"]["app_guid"] for e in bindings), None)
        assert application_id in ids

    def delete(self, client: HttpClient=None, force=False):
        if self._is_deleted is True and force is False:
            return

        try:
            api.delete_service(service_id=self.id, client=self._get_client(client))
            self._set_deleted(True)
        except UnexpectedResponseError:
            raise

    @classmethod
    def _metadata_to_dict(cls, metadata):
        metadata_dict = {}
        if metadata is not None:
            for pair in metadata:
                metadata_dict.update({pair["key"]: pair["value"]})
        return metadata_dict

    @classmethod
    def _from_response(cls, response, client=None):
        metadata = cls._metadata_to_dict(response["metadata"])
        plan_id = metadata.get(cls.PLAN_ID_METADATA_KEY, None)
        assert plan_id is not None, "No service instance plan id found in the response"
        url = metadata.get(cls.URLS_METADATA_KEY, None)
        offering_id = response.get("classId")
        if offering_id is None:
            offering_id = response.get("offeringId")
        return cls(service_id=response["id"], plan_id=plan_id, offering_id=offering_id,
                   bindings=response["bindings"], state=response["state"], name=response["name"],
                   offering_label=response.get("serviceName", None), url=url, client=client)

    def _refresh(self, client: HttpClient=None):
        this_instance = self.get(service_id=self.id, client=self._get_client(client))
        assert this_instance is not None, "Instance {} not found on the list".format(self.name)
        self.state = this_instance.state
        self.url = this_instance.url

    def get_credentials(self, client=None):
        return api.get_service_credentials(service_id=self.id, client=self._get_client(client))

    def get_logs(self, client=None):
        return api.get_service_logs(service_id=self.id, client=self._get_client(client))

    @classmethod
    def _get_offering_id_and_plan_id_by_names(cls, offering_label: str, plan_name: str, client: HttpClient) -> tuple:
        """
        From the list of offerings, retrieve offering_id by label and plan_id by name.
        """
        response = api.get_offerings(client=client)

        # find offering in the response
        offering_data = next((i for i in response if i["name"] == offering_label), None)
        assert offering_data is not None, "No such offering {}".format(offering_label)

        # find plan in offering data
        plan_data = next((i for i in offering_data["offeringPlans"] if i["name"] == plan_name), None)
        assert plan_data is not None, "No such plan {} for offering {}".format(plan_name, offering_label)

        offering_id = offering_data["id"]
        plan_id = plan_data["id"]
        return offering_id, plan_id

    def cleanup(self):
        if self.state == TapEntityState.RUNNING:
            self.stop()
            self.ensure_stopped()
        self.delete()

    @classmethod
    def get_credentials(cls, service_id: str, client: HttpClient=None):
        return api.get_service_credentials(client=client, service_id=service_id)

    @classmethod
    def expose_urls(cls, service_id: str, should_expose: bool=True, client: HttpClient=None):
        return api.expose_service(client=client, service_id=service_id, should_expose=should_expose)

    @classmethod
    @retry(AssertionError, tries=5, delay=10)
    def ensure_responding(cls, url: str):
        r = requests.get(url)
        assert str(ApiServiceHttpStatus.CODE_OK) in str(r)


class AtkInstance(ServiceInstance):

    @classmethod
    def api_get_list_from_data_science_atk(cls, org_guid, client=None):
        raise NotImplemented("Not sure if/how it will be implemented for new TAP")
