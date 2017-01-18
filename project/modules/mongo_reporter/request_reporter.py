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

import time
from datetime import datetime

import pytest
from requests import PreparedRequest

import config
from modules.mongo_reporter._client import MockDbClient, DBClient
from modules.tap_logger import get_logger

logger = get_logger(__name__)


class RequestReporter:
    COLLECTION_NAME = 'request'

    def __init__(self):
        self.requests = []

        if self._log_requests():
            self._db_client = DBClient(uri=config.database_url)
        else:
            if config.database_url is None:
                logger.warning("Not writing results to a database - database_url not configured.")
            self._db_client = MockDbClient()

    @staticmethod
    def _log_requests():
        return config.log_requests and config.database_url and config.stress_run_id

    def add_request(self, request: dict):
        request['stress_run_id'] = config.stress_run_id
        logger.debug('New request logged: {}'.format(request))
        self.requests.append(request)

    def send_to_db(self, test_name):
        for request in self.requests:
            request['test_name'] = test_name
        logger.info('Sending logged requests to db ({} requests)'.format(len(self.requests)))
        for request in self.requests:
            self._db_client.insert(collection_name=self.COLLECTION_NAME, document=request)
        self.requests = []


request_reporter = RequestReporter()


def log_request(func: callable):

    def wrapper(self, request: PreparedRequest, timeout: int):
        request_info = {
            'date': datetime.now(),
            'method': request.method,
            'url': request.path_url
        }
        start_time = time.perf_counter()

        response = func(self, request=request, timeout=timeout)

        request_info['duration'] = time.perf_counter() - start_time
        request_info['status_code'] = response.status_code

        request_reporter.add_request(request_info)

        return response

    return wrapper


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    test_name = item.nodeid.split('::')[-1]
    request_reporter.send_to_db(test_name)
