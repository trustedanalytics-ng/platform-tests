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

from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client import HttpClientFactory, HttpClient


class ApiModelSuperclass(object):
    """
    Base class for all models which support both api-service and console.
    """

    def __init__(self, *, object_id: str, client: HttpClient=None):
        self.id = object_id
        self._client = client
        if self._client is None:
            self._client = self._get_default_client()

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        raise NotImplemented

    @classmethod
    def _list_from_response(cls, response: list, client: HttpClient):
        items = []
        for item in response:
            items.append(cls._from_response(item, client))
        return items

    @classmethod
    def _get_default_client(cls):
        return HttpClientFactory.get(ConsoleConfigurationProvider.get())

    def _get_client(self, client):
        if client is None:
            client = self._client
        return client
