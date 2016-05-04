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

from ..http_calls.platform import service_catalog


class ServiceBinding(object):
    COMPARABLE_ATTRIBUTES = ["guid", "app_guid", "service_instance_guid"]

    def __init__(self, guid, app_guid, service_instance_guid):
        self.guid = guid
        self.app_guid = app_guid
        self.service_instance_guid = service_instance_guid

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def _from_response(cls, response):
        entity = response["entity"]
        service_binding = cls(response["metadata"]["guid"], entity["app_guid"], entity["service_instance_guid"])
        return service_binding

    @classmethod
    def api_get_list(cls, app_guid, client=None):
        response = service_catalog.api_get_app_bindings(app_guid, client=client)
        service_bindings = []
        for instance in response:
            service_bindings.append(cls._from_response(instance))
        return service_bindings

    @classmethod
    def api_create(cls, app_guid, service_instance_guid, client=None):
        response = service_catalog.api_create_service_binding(app_guid, service_instance_guid, client)
        return cls._from_response(response)

    def api_delete(self):
        service_catalog.api_delete_service_binding(self.guid)
