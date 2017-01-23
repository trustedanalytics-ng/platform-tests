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
from unittest import mock
from unittest.mock import Mock

from bson import ObjectId

from modules.mongo_reporter._client import MockDbClient
from modules.mongo_reporter.request_reporter import RequestReporter, log_request, request_reporter
from tests.fixtures.assertions import assert_date_close_enough_to_now, assert_values_approximately_equal

SELF = mock.Mock()
TIMEOUT = 1
DURATION = .5
TEST_NAME = 'test_name'
TEST_STRESS_RUN_ID = str(ObjectId())


class MockRequest:
    method = 'GET'
    path_url = '/login'

TEST_NEW_REQUEST_INFO = {
    'date': datetime.now(),
    'method': MockRequest.method,
    'status_code': 200,
    'url': MockRequest.path_url
}

TEST_REQUEST_INFO = dict(TEST_NEW_REQUEST_INFO, stress_run_id=TEST_STRESS_RUN_ID)
TEST_REQUEST_INFO_IN_DB = dict(TEST_REQUEST_INFO, test_name=TEST_NAME)

class MockConfig:
    def __init__(self, database_url='db_url', stress_run_id=TEST_STRESS_RUN_ID, log_requests=True):
        self.database_url = database_url
        self.stress_run_id = stress_run_id
        self.log_requests = log_requests
        self.appstack_version = "test_appstack_version"
        self.tap_domain = "test_tap_domain"
        self.tap_infrastructure_type = "test_infrastructure_type"
        self.tap_version = "test_tap_version"
        self.kerberos = "test_kerberos"
        self.hatch_rate = "test_hatch_rate"
        self.num_clients = "test_num_clients"


@mock.patch('modules.mongo_reporter.request_reporter.config', MockConfig())
class TestRequestReporter(object):

    def test_collection_name_is_not_none(self):
        reporter = RequestReporter()
        assert reporter.COLLECTION_NAME == 'request', 'RequestReporter has no specified collection name'

    def test_request_list_should_be_initialized_empty(self):
        reporter = RequestReporter()
        assert len(reporter.requests) == 0, 'RequestReporter are initialized with non empty requests list'

    def test_use_mock_client_if_no_db_url(self):
        with mock.patch('modules.mongo_reporter.request_reporter.config', MockConfig(database_url=None)):
            reporter = RequestReporter()
            assert isinstance(reporter._db_client, MockDbClient), \
                'RequestReporter should use MockDbClient if no db url provided'

    def test_use_mock_client_if_no_stress_run_id(self):
        with mock.patch('modules.mongo_reporter.request_reporter.config', MockConfig(stress_run_id=None)):
            reporter = RequestReporter()
            assert isinstance(reporter._db_client, MockDbClient), \
                'RequestReporter should use MockDbClient if no stress run id provided'

    def test_use_mock_client_if_log_requests_is_false(self):
        with mock.patch('modules.mongo_reporter.request_reporter.config', MockConfig(log_requests=False)):
            reporter = RequestReporter()
            assert isinstance(reporter._db_client, MockDbClient), \
                'RequestReporter should use MockDbClient if PT_LOG_REQUESTS flag is not set'

    def test_add_request(self):
        reporter = RequestReporter()
        reporter.add_request(TEST_NEW_REQUEST_INFO)
        assert len(reporter.requests) == 1, "Request isn't logged to RequestReporter"
        assert reporter.requests[0] == TEST_REQUEST_INFO, \
            'RequestReporter assign incorrect stress run id to request info'

    @mock.patch('modules.mongo_reporter.request_reporter.DBClient.insert')
    def test_send_to_db(self, mock_insert_method):
        reporter = RequestReporter()
        reporter.add_request(TEST_NEW_REQUEST_INFO)
        reporter.send_to_db(TEST_NAME)
        mock_insert_method.assert_called_once_with(collection_name='request', document=TEST_REQUEST_INFO_IN_DB)

    @mock.patch('modules.mongo_reporter.request_reporter.DBClient.insert')
    def test_clean_request_lists_after_sending_to_db(self, mock_insert_method):
        reporter = RequestReporter()
        reporter.add_request(TEST_NEW_REQUEST_INFO)
        assert len(reporter.requests) == 1, "Request isn't logged to RequestReporter"
        reporter.send_to_db(TEST_NAME)
        assert len(reporter.requests) == 0, 'RequestReporter.send_to_db() not clean RequestReporter.requests list'

    @mock.patch('modules.mongo_reporter.request_reporter.DBClient.insert')
    def test_send_no_request_info_if_no_request_logged(self, mock_insert_method):
        reporter = RequestReporter()
        reporter.send_to_db(TEST_NAME)
        assert not mock_insert_method.called


def mock_function(*args, **kwargs):
    time.sleep(DURATION)
    response = Mock()
    response.status_code = TEST_NEW_REQUEST_INFO['status_code']
    return response


@mock.patch('modules.mongo_reporter.request_reporter.config', MockConfig())
def test_log_request_decorator():
    request_reporter.requests = []

    decorated_func = log_request(mock_function)
    decorated_func('self', request=MockRequest, timeout=TIMEOUT)

    assert len(request_reporter.requests) == 1, '@log_request does not add request to request_report'

    logged_request = request_reporter.requests[0]

    assert_date_close_enough_to_now(logged_request['date'], epsilon=.8)
    assert_values_approximately_equal(logged_request['duration'], DURATION, epsilon=.5)
    assert logged_request['method'] == TEST_REQUEST_INFO['method']
    assert logged_request['status_code'] == TEST_REQUEST_INFO['status_code']
    assert logged_request['stress_run_id'] == TEST_REQUEST_INFO['stress_run_id']
    assert logged_request['url'] == TEST_REQUEST_INFO['url']
