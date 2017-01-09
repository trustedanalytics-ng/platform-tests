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

from modules.constants import TapMessage
from modules.http_client import HttpClient
import modules.http_calls.platform.api_service as api
from ._api_model_superclass import ApiModelSuperclass
from ._tap_object_superclass import TapObjectSuperclass


class Binding(ApiModelSuperclass, TapObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["app_id", "service_instance_id"]

    def __init__(self, *, app_id, service_instance_id, client: HttpClient=None):
        super().__init__(object_id=hash(app_id + service_instance_id), client=client)
        self.app_id = app_id
        self.service_instance_id = service_instance_id

    @classmethod
    def get_list(cls, *, app_id: str, client: HttpClient=None) -> list:
        if client is None:
            client = cls._get_default_client()
        response = api.get_app_bindings(client=client, app_id=app_id)
        if response is None:
            bindings = []
        else:
            bindings = cls._list_from_response(response, client)
        return bindings

    @classmethod
    def _find_on_list(cls, app_id: str, service_instance_id: str, client: HttpClient):
        bindings = cls.get_list(app_id=app_id, client=client)
        assert len(bindings) > 0, "No bindings for app {} found".format(app_id)
        binding = next((b for b in bindings if b.service_instance_id == service_instance_id), None)
        assert binding is not None, "Binding of app {} to instance {} not found".format(app_id, service_instance_id)
        return binding

    @classmethod
    def create(cls, context, *, app_id: str, service_instance_id: str, client: HttpClient=None):
        if client is None:
            client = cls._get_default_client()
        response = api.bind_app(client=client, app_id=app_id, service_instance_id=service_instance_id)
        assert response["message"] == TapMessage.SUCCESS
        binding = cls._find_on_list(app_id=app_id, service_instance_id=service_instance_id, client=client)
        context.test_objects.append(binding)
        return binding

    def delete(self, client: HttpClient=None):
        api.unbind_app(app_id=self.app_id, service_instance_id=self.service_instance_id,
                       client=self._get_client(client))

    def __repr__(self):
        return "{} (app_id={}, service_instance_id={})".format(self.__class__.__name__,
                                                               self.app_id, self.service_instance_id)

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        entity = response["entity"]
        binding = cls(app_id=entity["app_guid"], service_instance_id=entity["service_instance_guid"], client=client)
        return binding
