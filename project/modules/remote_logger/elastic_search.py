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

import os
from datetime import datetime

import requests

from project.modules.remote_logger.config import Config
from .log_provider_configuration import LogProviderConfiguration
from .elastic_search_response_converter import ElasticSearchResponseConverter
from config import ng_socks_proxy_port


class ElasticSearch(object):
    """Elastic search requests manager."""

    MAX_PAGE_LIMIT = 10000

    def __init__(self, configuration: LogProviderConfiguration):
        self.__configuration = configuration
        self.__load_query_template()
        self.__last_total_count = 0

    def is_log_ready(self):
        """Check if there are logs for given configuration and they are ready to read"""
        query = self.__get_query(limit=0, offset=0)
        response = self.__request(query)
        last_total_count = self.__last_total_count
        total_count = response["hits"]["total"]
        self.__last_total_count = total_count
        return 0 < last_total_count == total_count

    def get_log(self):
        """Read all available logs for given configuration."""
        if self.__last_total_count > self.MAX_PAGE_LIMIT:
            raise ElasticSearchResultPaginationNotImplementedException()
        query = self.__get_query(limit=self.__last_total_count, offset=0)
        response = self.__request(query)
        return ElasticSearchResponseConverter.convert(response)

    def __get_query(self, limit=0, offset=0):
        """Prepare search query based on query template and given configuration."""
        return self.__query_template \
            .replace("_LIMIT_", str(limit)) \
            .replace("_OFFSET_", str(offset)) \
            .replace("_DATE_FROM_", str(self.__configuration.from_date)) \
            .replace("_DATE_TO_", str(self.__configuration.to_date)) \
            .replace("_APP_NAME_", self.__configuration.app_name)

    def __load_query_template(self):
        """Load query template from file."""
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "elastic_search.query"), 'r') as file:
            self.__query_template = file.read()

    def __request(self, query):
        """Make search request and return response converted into json object."""
        proxies = {'http': "socks5://localhost:{}".format(ng_socks_proxy_port)}
        response = requests.post(
            url=self.__request_url(),
            timeout=Config.ELASTIC_SEARCH_REQUEST_TIMEOUT,
            data=query,
            proxies=proxies
        )
        if not response.ok:
            raise ElasticSearchUnexpectedResponseException(response.text)
        return response.json()

    @staticmethod
    def __request_url():
        """Create request url address."""
        date = datetime.now().strftime("%Y.%m.%d")
        return Config.ELASTIC_QUERY_URL.format(Config.ELASTIC_SEARCH_HOST, Config.ELASTIC_SEARCH_HOST_PORT, date)


class ElasticSearchResultPaginationNotImplementedException(Exception):
    def __init__(self):
        super().__init__("Results total count is higher than MAX_PAGE_LIMIT and need pagination to get all results.")


class ElasticSearchUnexpectedResponseException(Exception):
    def __init__(self, message=None):
        super().__init__(message)
