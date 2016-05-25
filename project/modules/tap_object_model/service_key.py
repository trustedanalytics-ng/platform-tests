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

from ..test_names import generate_test_object_name
from ..http_calls.platform import service_catalog


@functools.total_ordering
class ServiceKey(object):

    COMPARABLE_ATTRIBUTES = ["guid", "name", "credentials", "service_instance_guid"]

    def __init__(self, guid, name, credentials, service_instance_guid):
        self.guid = guid
        self.name = name
        self.credentials = credentials or []
        self.service_instance_guid = service_instance_guid

    def __repr__(self):
        return "{0} (guid={1}, name={2})".format(self.__class__.__name__, self.guid, self.name)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    def __hash__(self):
        return hash((self.guid, self.name, self.credentias, self.service_instance_guid))

    def api_delete(self, client=None):
        service_catalog.api_delete_service_key(service_key_guid=self.guid, client=client)

    def cleanup(self):
        self.api_delete()

    @classmethod
    def api_create(cls, service_instance_guid, name=None, client=None):
        service_key_name = name or generate_test_object_name()
        response = service_catalog.api_create_service_key(service_instance_guid, service_key_name, client)
        return cls(guid=response["guid"], name=response["name"], credentials=response["credentials"],
                   service_instance_guid=response["service_instance_guid"])
