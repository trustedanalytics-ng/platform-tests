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

from ..http_calls import cloud_foundry as cf


@functools.total_ordering
class ServiceBroker(object):

    COMPARABLE_ATTRIBUTES = ["guid", "name", "space_guid"]

    def __init__(self, guid, name, url=None, created_at=None, updated_at=None, broker_url=None, auth_username=None):
        self.guid, self.name, self.url = guid, name, url
        self.created_at, self.updated_at, self.broker_url = created_at, updated_at, broker_url
        self.auth_username = auth_username

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def _from_cf_api_response(cls, broker_data):
        metadata = broker_data["metadata"]
        entity = broker_data["entity"]
        return cls(guid=metadata["guid"], name=entity["name"], url=metadata["url"],
                   created_at=metadata["created_at"], updated_at=metadata["updated_at"],
                   broker_url=entity["broker_url"], auth_username=entity["auth_username"])

    @classmethod
    def cf_api_get_list(cls, space_guid):
        service_broker_data = cf.cf_api_get_service_brokers(space_guid)
        service_brokers = []
        for data in service_broker_data:
            service_brokers.append(cls._from_cf_api_response(data))
        return service_brokers
