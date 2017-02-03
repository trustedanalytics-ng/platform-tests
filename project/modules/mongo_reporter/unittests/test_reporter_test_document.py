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
from modules.mongo_reporter.reporter import MongoReporter
from modules.mongo_reporter._client import DBClient


class Dummy:
    pass


TEST_DOCSTRING = "test-docstring"
TEST_COMPONENTS = ("abc", "def")
TEST_DEFECTS = ("lorem", "ipsum")
TEST_LOG = "test-log"
TEST_PRIORITY = "test-priority"
TEST_KEYWORDS = ("a", "b", "c")
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
report.keywords = TEST_KEYWORDS

TEST_COMMON_REPORT = {
    "components": TEST_COMPONENTS,
    "docstring": TEST_DOCSTRING,
    "defects": ", ".join(TEST_DEFECTS),
    "priority": TEST_PRIORITY,
    "tags": ", ".join(TEST_KEYWORDS),
    "log": TEST_LOG,
    "run_id": TEST_RUN_ID,
    "stacktrace": TEST_STACKTRACE,
    "test_type": TEST_TEST_TYPE,
}


def _marker_args_from_item(self, item, marker_name):
    if marker_name == "bugs":
        return TEST_DEFECTS
    elif marker_name == "components":
        return TEST_COMPONENTS


@mock.patch.multiple("modules.mongo_reporter.reporter.MongoReporter",
                     _get_test_docstring=lambda *args, **kwargs: TEST_DOCSTRING,
                     _get_test_type_from_report=lambda *args, **kwargs: TEST_TEST_TYPE,
                     _marker_args_from_item=_marker_args_from_item,
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
        assert set(TEST_COMMON_REPORT.items()).issubset(set(test_document.items()))
        assert test_document["status"] == TEST_STATUS

        if not failed_by_setup:
            assert test_document["duration"] == report.duration
            assert test_document["name"] == report.nodeid
            assert test_document["order"] == TEST_TEST_COUNT
        else:
            assert test_document["duration"] == 0.0
            assert test_document["name"] == "{}: failed on setup".format(report.nodeid)
            assert "order" not in test_document

    def test_on_fixture_error(self):
        reporter = MongoReporter(run_id=TEST_RUN_ID)
        test_document, status = reporter._on_fixture_error(report=report, item=item, log=TEST_LOG)
        assert status == MongoReporter._RESULT_FAIL
        assert set(TEST_COMMON_REPORT.items()).issubset(set(test_document.items()))
        assert test_document["status"] == MongoReporter._RESULT_FAIL
        assert test_document["name"] == "{}: {} error".format(report.nodeid, report.when)

    def test_on_fixture_skipped(self):
        reporter = MongoReporter(run_id=TEST_RUN_ID)
        test_document, status = reporter._on_fixture_skipped(report=report, item=item, log=TEST_LOG)
        assert status == MongoReporter._RESULT_SKIPPED
        assert set(TEST_COMMON_REPORT.items()).issubset(set(test_document.items()))
        assert test_document["name"] == "{}: skipped".format(report.nodeid)
        assert test_document["status"] == status

    @pytest.mark.parametrize("report_passed,report_failed,report_skipped",
                             [(True, False, False), (False, True, False), (False, False, True)],
                             ids=("report_passed", "report_failed", "report_skipped"))
    @mock.patch("modules.mongo_reporter.reporter.config.database_url", "test_uri")
    def test_log_report_on_call(self, mock_db_client, report_passed, report_failed, report_skipped):
        report.when = "call"
        report.passed = report_passed
        report.failed = report_failed
        report.skipped = report_skipped

        with mock.patch("modules.mongo_reporter.base_reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after["test_count"] == run_document_before["test_count"] + 1
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 1
            assert test_documents[0]["name"] == report.nodeid
            assert test_documents[0]["status"] == TEST_STATUS

    @pytest.mark.parametrize(
        "report_when,report_passed,report_failed,report_skipped,expected_test_status,expected_test_name",
        [("setup", False, True, False, MongoReporter._RESULT_FAIL, "{}: setup error".format(report.nodeid)),
         ("setup", False, False, True, MongoReporter._RESULT_SKIPPED, "{}: skipped".format(report.nodeid)),
         ("teardown", False, True, False, MongoReporter._RESULT_FAIL, "{}: teardown error".format(report.nodeid)),
         ("teardown", False, False, True, MongoReporter._RESULT_SKIPPED, "{}: skipped".format(report.nodeid))],
        ids=("on_setup_report_error", "on_setup_report_skipped",
             "on_teardown_report_failed", "on_teardown_report_skipped"))
    @mock.patch("modules.mongo_reporter.reporter.config.database_url", "test_uri")
    def test_log_report_on_fixture_one_document(self, mock_db_client, report_when, report_passed, report_failed,
                                                report_skipped, expected_test_status, expected_test_name):
        report.when = report_when
        report.passed = report_passed
        report.failed = report_failed
        report.skipped = report_skipped

        with mock.patch("modules.mongo_reporter.base_reporter.DBClient", mock_db_client):
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
            if report_skipped:
                assert test_documents[0]["status"] == MongoReporter._RESULT_SKIPPED
            else:
                assert test_documents[0]["status"] == MongoReporter._RESULT_FAIL

    @pytest.mark.parametrize("report_when", ("setup", "teardown"),
                             ids=("on_setup_report_passed", "on_teardown_report_passed"))
    @mock.patch("modules.mongo_reporter.reporter.config.database_url", "test_uri")
    def test_log_report_no_update(self, mock_db_client, report_when):
        report.when = report_when
        report.passed = True
        report.failed = False
        report.skipped = False

        with mock.patch("modules.mongo_reporter.base_reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after == run_document_before
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 0

    @mock.patch("modules.mongo_reporter.reporter.config.database_url", "test_uri")
    def test_log_report_two_documents(self, mock_db_client):
        report.when = "setup"
        report.passed = False
        report.failed = True
        report.skipped = False

        with mock.patch("modules.mongo_reporter.base_reporter.DBClient", mock_db_client):
            reporter = MongoReporter()
            run_document_before = copy.deepcopy(reporter._mongo_run_document)
            reporter.log_report(report=report, item=item)
            run_document_after = reporter._mongo_run_document
            assert run_document_after["test_count"] == run_document_before["test_count"]
            test_documents = self._get_test_result_documents(reporter)
            assert len(test_documents) == 1
            fixture_document = next((d for d in test_documents if d["status"] == MongoReporter._RESULT_FAIL), None)
            assert fixture_document is not None
            assert fixture_document["name"] == "{}: setup error".format(report.nodeid)
