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

import copy
from unittest import mock

import bson
import mongomock

import pytest
from modules.mongo_reporter._reporter import MongoReporter, DBClient


class Dummy:
    pass


TEST_DOCSTRING = "test-docstring"
TEST_ITEMS = ("abc", "def")
TEST_LOG = "test-log"
TEST_PRIORITY = "test-priority"
TEST_RUN_ID = bson.ObjectId()
TEST_STACKTRACE = "test-stacktrace"
TEST_TEST_COUNT = 14
TEST_STATUS = MongoReporter._RESULT_PASS
TEST_TEST_TYPE = "test-type"
item = Dummy()
report = Dummy()
report.nodeid = "test-name"
report.when = "then"
report.duration = 0.123
report.keywords = ("a", "b", "c")


@mock.patch.multiple("modules.mongo_reporter._reporter.MongoReporter",
                     _get_test_docstring=lambda *args, **kwargs: TEST_DOCSTRING,
                     _get_test_type_from_report=lambda *args, **kwargs: TEST_TEST_TYPE,
                     _marker_args_from_item=lambda *args, **kwargs: TEST_ITEMS,
                     _priority_from_report=lambda *args, **kwargs: TEST_PRIORITY,
                     _stacktrace_from_report=lambda *args, **kwargs: TEST_STACKTRACE,
                     _test_status_from_report=lambda *args, **kwargs: TEST_STATUS)
class TestReporterTestDocument:

    @pytest.fixture(scope="function")
    def mock_db_client(self):
        class MockClient(DBClient):
            def __init__(self, *args, **kwargs):
                self.database = mongomock.MongoClient().db
        return MockClient

    def _get_test_result_documents(self, reporter):
        return [d for d in reporter._db_client.database[MongoReporter._TEST_RESULT_COLLECTION_NAME].find()]

    @pytest.mark.parametrize("failed_by_setup", (False, True))
    def test_on_test_not_failed_by_setup(self, failed_by_setup):
        reporter = MongoReporter(run_id=TEST_RUN_ID)
        reporter._mongo_run_document["test_count"] = TEST_TEST_COUNT
        test_document, status = reporter._on_test(report=report, item=item, log=TEST_LOG,
                                                  failed_by_setup=failed_by_setup)
        assert status == TEST_STATUS
        assert test_document["components"] == TEST_ITEMS
        assert test_document["defects"] == ", ".join(TEST_ITEMS)
        assert test_document["docstring"] == TEST_DOCSTRING
        assert test_document["log"] == TEST_LOG
        assert test_document["priority"] == TEST_PRIORITY
        assert test_document["run_id"] == TEST_RUN_ID
        assert test_document["stacktrace"] == TEST_STACKTRACE
        assert test_document["status"] == TEST_STATUS
        assert test_document["tags"] == ", ".join(report.keywords)
        assert test_document["test_type"] == TEST_TEST_TYPE

        if not failed_by_setup:
            assert test_document["duration"] == report.duration
            assert test_document["name"] == report.nodeid
            assert test_document["order"] == TEST_TEST_COUNT

        else:
            assert test_document["duration"] == 0.0
            assert test_document["name"] == "{}: failed on setup".format(report.nodeid)
            assert "order" not in test_document

    @pytest.mark.parametrize("reason,expected_status,expected_name",
                             [("error", MongoReporter._RESULT_FAIL, "{}: {} error".format(report.nodeid, report.when)),
                              ("skipped", MongoReporter._RESULT_SKIPPED, "{}: skipped".format(report.nodeid))],
                             ids=("error", "skipped"))
    def test_on_fixture(self, reason, expected_status, expected_name):
        reporter = MongoReporter(run_id=TEST_RUN_ID)
        test_document, status = reporter._on_fixture(report=report, item=item, reason=reason, log=TEST_LOG)
        assert status == expected_status
        assert test_document["components"] == TEST_ITEMS
        assert test_document["docstring"] == TEST_DOCSTRING
        assert test_document["log"] == TEST_LOG
        assert test_document["name"] == expected_name
        assert test_document["run_id"] == TEST_RUN_ID
        assert test_document["stacktrace"] == TEST_STACKTRACE
        assert test_document["test_type"] == TEST_TEST_TYPE

    @pytest.mark.parametrize("report_passed,report_failed,report_skipped",
                             [(True, False, False), (False, True, False), (False, False, True)],
                             ids=("report_passed", "report_failed", "report_skipped"))
    @mock.patch("modules.mongo_reporter._reporter.config.database_url", "test_uri")
    def test_log_report_on_call(self, mock_db_client, report_passed, report_failed, report_skipped):
        report.when = "call"
        report.passed = report_passed
        report.failed = report_failed
        report.skipped = report_skipped

        with mock.patch("modules.mongo_reporter._reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after["test_count"] == run_document_before["test_count"] + 1
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 1
            assert test_documents[0]["name"] == report.nodeid
            assert test_documents[0]["status"] == TEST_STATUS

    @pytest.mark.parametrize("report_when,report_passed,report_failed,report_skipped,expected_test_status,expected_test_name",
                             [("setup", False, False, True, MongoReporter._RESULT_SKIPPED, "{}: skipped".format(report.nodeid)),
                              ("teardown", False, True, False, MongoReporter._RESULT_FAIL, "{}: teardown error".format(report.nodeid)),
                              ("teardown", False, False, True, MongoReporter._RESULT_SKIPPED, "{}: skipped".format(report.nodeid))],
                             ids=("on_setup_report_skipped", "on_teardown_report_failed", "on_teardown_report_skipped"))
    @mock.patch("modules.mongo_reporter._reporter.config.database_url", "test_uri")
    def test_log_report_on_fixture_one_document(self, mock_db_client, report_when, report_passed, report_failed,
                                                report_skipped, expected_test_status, expected_test_name):
        report.when = report_when
        report.passed = report_passed
        report.failed = report_failed
        report.skipped = report_skipped

        with mock.patch("modules.mongo_reporter._reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after["test_count"] == run_document_before["test_count"]
            if expected_test_status == MongoReporter._RESULT_FAIL:
                assert run_document_after["status"] == MongoReporter._RESULT_FAIL
            else:
                assert run_document_after["status"] == run_document_before["status"]
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 1
            assert test_documents[0]["name"] == expected_test_name
            assert "status" not in test_documents[0]

    @pytest.mark.parametrize("report_when", ("setup", "teardown"),
                             ids=("on_setup_report_passed", "on_teardown_report_passed"))
    @mock.patch("modules.mongo_reporter._reporter.config.database_url", "test_uri")
    def test_log_report_no_update(self, mock_db_client, report_when):
        report.when = report_when
        report.passed = True
        report.failed = False
        report.skipped = False

        with mock.patch("modules.mongo_reporter._reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after == run_document_before
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 0

    @mock.patch("modules.mongo_reporter._reporter.config.database_url", "test_uri")
    def test_log_report_two_documents(self, mock_db_client):
        report.when = "setup"
        report.passed = False
        report.failed = True
        report.skipped = False

        with mock.patch("modules.mongo_reporter._reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after["test_count"] == run_document_before["test_count"]
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 1
            fixture_document = next((d for d in test_documents if "status" not in d), None)
            assert fixture_document is not None
            assert fixture_document["name"] == "{}: setup error".format(report.nodeid)
