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

from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client import HttpClientFactory, HttpClient


@functools.total_ordering
class ApiModelSuperclass(object):
    """
    Base class for all models which support both api-service and console.
    """
    _COMPARABLE_ATTRIBUTES = []

    def __init__(self, *, item_id: str, client: HttpClient=None):
        self.id = item_id
        self._client = client
        if self._client is None:
            self._client = self._get_default_client()

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        raise self.id < other.id

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self._COMPARABLE_ATTRIBUTES))

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        raise NotImplemented

    @classmethod
    def _list_from_response(cls, response: list, client: HttpClient) -> list:
        items = []
        for item in response:
            instance = cls._from_response(item, client)
            items.append(instance)
        return items

    @classmethod
    def _get_default_client(cls):
        return HttpClientFactory.get(ConsoleConfigurationProvider.get())

    def _get_client(self, client):
        if client is None:
            return self._client
        return client

    def delete(self):
        raise NotImplemented

    def cleanup(self):
        self.delete()