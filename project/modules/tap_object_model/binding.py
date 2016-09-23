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

from modules.http_client import HttpClientFactory
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from ..http_calls.platform import api_service


class Binding(object):
    COMPARABLE_ATTRIBUTES = ["app_guid", "service_instance_guid", "service_instance_name"]

    def __init__(self, app_guid, service_instance_guid, service_instance_name):
        self.app_guid = app_guid
        self.service_instance_guid = service_instance_guid
        self.service_instance_name = service_instance_name

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.app_guid < other.app_guid and self.service_instance_guid < other.service_instance_guid

    @classmethod
    def _from_response(cls, response):
        entity = response["entity"]
        binding = cls(entity["app_guid"], entity["service_instance_guid"], entity["service_instance_name"])
        return binding

    @classmethod
    def get_list(cls, app_guid, client=None):
        client = cls._get_client(client)
        response = api_service.get_app_bindings(app_guid, client)
        bindings = []
        # Response is None when there are no bindings
        if response is not None:
            for instance in response:
                bindings.append(cls._from_response(instance))
        return bindings

    @classmethod
    def find_on_list(cls, app_guid, service_instance_guid, client=None):
        client = cls._get_client(client)
        service_bindings = cls.get_list(app_guid, client)
        binding_found = None
        for binding in service_bindings:
            if binding.app_guid == app_guid and binding.service_instance_guid == service_instance_guid:
                binding_found = binding
        assert binding_found is not None,\
            "Binding of app {} and instance {} doesn't exists".format(app_guid, service_instance_guid)
        return binding_found

    @classmethod
    def create(cls, context, app_guid, service_instance_guid, client=None):
        client = cls._get_client(client)
        response = api_service.bind(service_instance_guid, app_guid, client)
        assert response["message"] == "success"
        binding = cls.find_on_list(app_guid, service_instance_guid, client)
        context.bindings.append(binding)
        return binding

    def delete(self, client=None):
        client = self._get_client(client)
        api_service.unbind(self.app_guid, self.service_instance_guid, client)

    def cleanup(self):
        self.delete()

    @staticmethod
    def _get_client(client=None):
        if client is None:
            configuration = ConsoleConfigurationProvider.get()
            client = HttpClientFactory.get(configuration)
        return client
