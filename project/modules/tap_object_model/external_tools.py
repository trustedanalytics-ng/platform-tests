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
from urllib.parse import urlparse

import requests

from configuration.config import CONFIG
from ..exceptions import UnexpectedResponseError
from ..http_calls import platform as api
from ..tap_logger import get_logger


logger = get_logger(__name__)


@functools.total_ordering
class ExternalTools(object):

    def __init__(self, name, url, available, category):
        self.name = name
        self.url = url
        self.available = available
        self.category = category
        self._session = requests.session()
        self._session.verify = CONFIG["ssl_validation"]

    def __eq__(self, other):
        return self.name == other.name and self.url == other.url and self.available == other.available

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash((self.name, self.url, self.available))

    def __repr__(self):
        return "{} {}".format(self.__class__.__name__, self.name)

    @property
    def should_have_url(self):
        return self.category == "visualizations"

    @classmethod
    def api_get_external_tools(cls, client=None):
        response = api.api_get_external_tools(client)
        tools_list = []
        tools = response["external_tools"]
        for tool_category, tool_list in tools.items():
            for tool_data in tool_list:
                tool = cls(name=tool_data["name"], url=tool_data["url"], available=tool_data["available"],
                           category=tool_category)
                tools_list.append(tool)
        return tools_list

    def send_request(self, method="GET"):
        parsed_url = urlparse(self.url)
        if not (parsed_url.scheme and parsed_url.hostname):
            raise AssertionError("{} url is invalid: {}".format(self, self.url))
        url = "{}://{}".format(parsed_url.scheme, parsed_url.hostname)
        request = self._session.prepare_request(requests.Request(method=method.upper(), url=url))
        response = self._session.send(request)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        return response.text

