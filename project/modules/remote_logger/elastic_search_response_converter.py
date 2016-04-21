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

from json import loads
from os import linesep


class ElasticSearchResponseConverter(object):
    """Convert json response into well formatted string."""

    @classmethod
    def convert(cls, response):
        """Convert json response to string format."""
        cls.__validate_key("hits", response)
        cls.__validate_key("hits", response["hits"])
        result = ""
        for log in response["hits"]["hits"]:
            result += cls.__convert_hits(log)
        return result

    @classmethod
    def __convert_hits(cls, hits):
        """Convert json hits into string."""
        cls.__validate_key("_source", hits)
        cls.__validate_key("@message", hits["_source"])
        message = loads(hits["_source"]["@message"])
        cls.__validate_key("msg", message)
        return "{}{}".format(message["msg"], linesep)

    @staticmethod
    def __validate_key(key, data):
        """Check if given key exists in response data."""
        if key not in data:
            raise ElasticSearchResponseConverterMissingKeyException(key)


class ElasticSearchResponseConverterMissingKeyException(Exception):
    TEMPLATE = "Response json key: {} is missing."

    def __init__(self, message=None):
        super().__init__(self.TEMPLATE.format(message))
