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
from datetime import datetime
import os
import socket
from unittest import mock

from bson import ObjectId
import pytest

from modules.constants import Path
from modules.mongo_reporter._reporter import MongoReporter, _MockDbClient

MOCK_BUMPVERSION_PATH = os.path.join("modules", "mongo_reporter", "unittests", "fixtures", "mock_bumpversion")
assert os.path.isfile(MOCK_BUMPVERSION_PATH)
MOCK_BUMPVERSION_BAD_PATH = os.path.join("modules", "mongo_reporter", "unittests", "fixtures", "mock_bumpversion_bad")
assert os.path.isfile(MOCK_BUMPVERSION_BAD_PATH)

TEST_RUN_ID = ObjectId()


class MockClient:
    def __init__(self, *args, **kwargs): pass
    insert = mock.Mock(return_value=TEST_RUN_ID)
    replace = lambda *args, **kwargs: None


class MockConfig:
    appstack_version = "test_appstack_version"
    database_url = "test_uri"
    tap_domain = "test_tap_domain"
    tap_infrastructure_type = "test_infrastructure_type"
    tap_version = "test_tap_version"
    kerberos = "test_kerberos"
    tap_build_number = 9876


class MockTeamcityConfiguration:
    GET_VALUE = "test_str"
    GETINT_VALUE = 1
    GET_ALL_VALUE = {"a": 1, "b": 2}

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.GET_VALUE

    @classmethod
    def getint(cls, *args, **kwargs):
        return cls.GETINT_VALUE

    @classmethod
    def get_all(cls, *args, **kwargs):
        return cls.GET_ALL_VALUE


@mock.patch("modules.mongo_reporter._reporter.DBClient", MockClient)
@mock.patch("modules.mongo_reporter._reporter.TeamCityConfiguration", MockTeamcityConfiguration)
class TestReporter(object):

    @pytest.fixture(scope="function")
    def dummy_class(self):
        class Dummy: pass
        return Dummy

    @pytest.fixture(scope="function")
    def mock_platform(self, monkeypatch):
        _mock_platform = mock.Mock()
        monkeypatch.setattr("modules.mongo_reporter._tap_info.PlatformInfo.get", _mock_platform)
        monkeypatch.setattr("modules.mongo_reporter._tap_info.config", MockConfig)
        return _mock_platform

    def _assert_all_keys_equal_except(self, document_a: dict, document_b: dict, *args):
        for k, v in document_a.items():
            if k not in args:
                assert v == document_b[k], "Value of {} key changed".format(k)

    def _assert_date_close_enough_to_now(self, date, epsilon=0.1):
        assert abs(date - datetime.now()).total_seconds() < epsilon

    @mock.patch("modules.mongo_reporter._reporter.config", MockConfig)
    def test_init_run_document(self, mock_platform):
        TEST_VERSION = "test.version"
        with mock.patch("modules.mongo_reporter._reporter.MongoReporter._get_test_version",
                        lambda *args, **kwargs: TEST_VERSION):
            run_document = MongoReporter()._mongo_run_document

        # values from config
        assert run_document["appstack_version"] == MockConfig.appstack_version
        assert run_document["environment"] == MockConfig.tap_domain
        assert run_document["environment_version"] == MockConfig.tap_version
        assert run_document["infrastructure_type"] == MockConfig.tap_infrastructure_type
        assert run_document["kerberos"] == MockConfig.kerberos
        # values from TeamCityConfiguration
        assert run_document["parameters"]["configuration_parameters"] == MockTeamcityConfiguration.GET_ALL_VALUE
        assert run_document["teamcity_build_id"] == MockTeamcityConfiguration.GETINT_VALUE
        assert run_document["teamcity_server_url"] == MockTeamcityConfiguration.GET_VALUE
        # other dynamic values
        self._assert_date_close_enough_to_now(run_document["start_date"])
        assert run_document["started_by"] == socket.gethostname()
        assert run_document["test_version"] == TEST_VERSION
        assert run_document["parameters"]["environment_variables"] == os.environ
        assert run_document["tap_build_number"] == MockConfig.tap_build_number
        # non-dynamic values
        assert run_document["end_date"] is None
        assert run_document["finished"] is False
        assert run_document["log"] == ""
        assert run_document["platform_components"] == []
        assert run_document["result"] == {MongoReporter._RESULT_PASS: 0, MongoReporter._RESULT_FAIL: 0,
                                          MongoReporter._RESULT_SKIPPED: 0, MongoReporter._RESULT_UNKNOWN: 0}
        assert run_document["status"] == MongoReporter._RESULT_PASS
        assert run_document["test_count"] == 0
        assert run_document["total_test_count"] == 0
        assert run_document["components"] == []
        assert run_document["environment_availability"] is True
        assert run_document["test_type"] is None

    @mock.patch("modules.mongo_reporter._reporter.config.database_url", "test_uri")
    def test_init_run_id_is_set(self):
        reporter = MongoReporter()
        assert reporter._run_id == TEST_RUN_ID

    @mock.patch("modules.mongo_reporter._reporter.config.database_url", None)
    def test_init_no_database_url(self):
        reporter = MongoReporter()
        assert isinstance(reporter._db_client, _MockDbClient)

    @mock.patch("modules.mongo_reporter._reporter.config.database_url", "test_uri")
    def test_init_database_url_set(self):
        reporter = MongoReporter()
        assert isinstance(reporter._db_client, MockClient)

    def test_init_run_id(self):
        run_id = ObjectId()
        reporter = MongoReporter(run_id=run_id)
        assert reporter._run_id == run_id

    def test_report_components(self):
        TEST_COMPONENTS = ["a", "b", "c"]
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter.report_components(TEST_COMPONENTS)
        document_after = reporter._mongo_run_document
        self._assert_all_keys_equal_except(document_before, document_after, "components")
        assert sorted(document_after["components"]) == sorted(TEST_COMPONENTS)

    def test_report_test_type(self):
        RUN_TYPE_GET_VALUE = "test-type"
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        with mock.patch("modules.mongo_reporter._reporter.RunType.get", lambda *args, **kwargs: RUN_TYPE_GET_VALUE):
            reporter.report_test_type("xxx")
        document_after = reporter._mongo_run_document
        self._assert_all_keys_equal_except(document_before, document_after, "test_type")
        assert reporter._mongo_run_document["test_type"] == RUN_TYPE_GET_VALUE

    def test_report_unavailable_environment(self):
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter.report_unavailable_environment()
        document_after = reporter._mongo_run_document
        self._assert_all_keys_equal_except(document_before, document_after, "environment_availability", "end_date",
                                           "finished")
        assert document_after["environment_availability"] is False
        self._assert_date_close_enough_to_now(document_after["end_date"])
        assert document_after["finished"] is True

    def test_on_run_end(self):
        TEST_COUNT = 123
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter._total_test_counter = TEST_COUNT
        reporter.on_run_end()
        document_after = reporter._mongo_run_document
        self._assert_all_keys_equal_except(document_before, document_after, "end_date", "total_test_count", "finished")
        self._assert_date_close_enough_to_now(document_after["start_date"])
        assert document_after["total_test_count"] == TEST_COUNT
        assert document_after["finished"] is True

    @mock.patch("modules.mongo_reporter._reporter.Path.bumpversion_file", MOCK_BUMPVERSION_PATH)
    def test_get_test_version(self):
        version = MongoReporter._get_test_version()
        assert version == "test.version"

    @mock.patch("modules.mongo_reporter._reporter.Path.bumpversion_file", "idontexist")
    def test_get_test_version_missing_bumpversion_file(self):
        with pytest.raises(AssertionError) as e:
            MongoReporter._get_test_version()
        assert "No such file" in e.value.msg

    @mock.patch("modules.mongo_reporter._reporter.Path.bumpversion_file", MOCK_BUMPVERSION_BAD_PATH)
    def test_get_test_version_bad_file(self):
        with pytest.raises(AssertionError) as e:
            MongoReporter._get_test_version()
        assert "Version not found" in e.value.msg

    def test_marker_args_from_item_no_args(self, dummy_class):
        class Item:
            def get_marker(self, *args, **kwargs):
                return dummy_class
        args = MongoReporter._marker_args_from_item(Item(), "name")
        assert args == tuple()

    def test_marker_args_from_item(self, dummy_class):
        TEST_ARGS = ("a", "b", "c")
        class Item:
            def get_marker(self, *args, **kwargs):
                dummy_class.args = TEST_ARGS
                return dummy_class
        args = MongoReporter._marker_args_from_item(Item(), "name")
        assert args == TEST_ARGS

    @pytest.mark.parametrize("keywords,expected_priority", [(("abc", "def"), None),
                                                            (("abc", "priority_kitten"), "kitten")],
                             ids=("no-priority-set", "priority_kitten"))
    def test_priority_from_report(self, dummy_class, keywords, expected_priority):
        dummy_class.keywords = keywords
        priority = MongoReporter._priority_from_report(dummy_class)
        assert priority == expected_priority

    def test_stacktrace_from_report_no_stacktrace(self, dummy_class):
        class Report:
            longrepr = dummy_class
        stacktrace = MongoReporter._stacktrace_from_report(Report())
        assert stacktrace is None

    def test_stacktrace_from_report(self, dummy_class):
        TEST_STACKTRACE = "test_stacktrace"
        class Report:
            dummy_class.reprtraceback = TEST_STACKTRACE
            longrepr = dummy_class
        stacktrace = MongoReporter._stacktrace_from_report(Report())
        assert stacktrace == TEST_STACKTRACE

    def test_test_type_from_report_directory_smoke(self, dummy_class):
        report = dummy_class
        report.fspath = Path.test_directories["test_smoke"]
        test_type = MongoReporter._get_test_type_from_report(report)
        assert test_type == MongoReporter._TEST_TYPE_SMOKE

    def test_test_type_from_report_directory_other(self, dummy_class):
        report = dummy_class
        report.fspath = "xx"
        with mock.patch("modules.mongo_reporter._reporter.MongoReporter._priority_from_report",
                        lambda *args, **kwargs: "kitten"):
            test_type = MongoReporter._get_test_type_from_report(report)
        assert test_type == MongoReporter._TEST_TYPE_OTHER

    @pytest.mark.parametrize("priority,expected_test_type", [("medium", MongoReporter._TEST_TYPE_REGRESSION),
                                                             ("high", MongoReporter._TEST_TYPE_REGRESSION),
                                                             ("low", MongoReporter._TEST_TYPE_OTHER),
                                                             ("kitten", MongoReporter._TEST_TYPE_OTHER)])
    def test_type_from_report_priority(self, priority, expected_test_type, dummy_class):
        with mock.patch("modules.mongo_reporter._reporter.MongoReporter._priority_from_report",
                        lambda *args, **kwargs: priority):
            test_type = MongoReporter._get_test_type_from_report(dummy_class)
        assert test_type == expected_test_type

    @pytest.mark.parametrize("report_attr_true,expected_test_status", [("passed", MongoReporter._RESULT_PASS),
                                                                       ("failed", MongoReporter._RESULT_FAIL),
                                                                       ("skipped", MongoReporter._RESULT_SKIPPED),
                                                                       ("other", MongoReporter._RESULT_UNKNOWN)],
                             ids=("pass", "fail", "skip", "unknown"))
    def test_test_status_from_report(self, dummy_class, report_attr_true, expected_test_status):
        for attr_name in ("passed", "failed", "skipped", "other"):
            setattr(dummy_class, attr_name, False)
        setattr(dummy_class, report_attr_true, True)
        test_status = MongoReporter._test_status_from_report(dummy_class)
        assert test_status == expected_test_status

    @pytest.mark.parametrize("run_status,test_status,expected_run_status",
                             [(MongoReporter._RESULT_PASS, MongoReporter._RESULT_PASS, MongoReporter._RESULT_PASS),
                              (MongoReporter._RESULT_PASS, MongoReporter._RESULT_FAIL, MongoReporter._RESULT_FAIL),
                              (MongoReporter._RESULT_FAIL, MongoReporter._RESULT_PASS, MongoReporter._RESULT_FAIL),
                              (MongoReporter._RESULT_PASS, MongoReporter._RESULT_SKIPPED, MongoReporter._RESULT_PASS),
                              (MongoReporter._RESULT_PASS, MongoReporter._RESULT_UNKNOWN, MongoReporter._RESULT_PASS)])
    def test_update_run_status(self, run_status, test_status, expected_run_status):
        reporter = MongoReporter()
        reporter._mongo_run_document["status"] = run_status
        run_document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter._update_run_status(result_document={}, test_status=test_status)
        run_document_after = reporter._mongo_run_document
        self._assert_all_keys_equal_except(run_document_before, run_document_after, "status", "result", "test_count")
        assert run_document_after["status"] == expected_run_status
        assert run_document_after["result"][test_status] == run_document_before["result"][test_status] + 1

    @pytest.mark.parametrize("increment_test_count", (True, False))
    def test_update_run_status_increment_test_count(self, increment_test_count):
        reporter = MongoReporter()
        run_document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter._update_run_status(result_document={}, test_status=MongoReporter._RESULT_PASS,
                                    increment_test_count=increment_test_count)
        run_document_after = reporter._mongo_run_document
        self._assert_all_keys_equal_except(run_document_before, run_document_after, "result", "test_count")
        if increment_test_count:
            assert run_document_after["test_count"] == run_document_before["test_count"] + 1
        else:
            assert run_document_after["test_count"] == run_document_before["test_count"]

    def test_save_test_run_no_run_id(self):
        reporter = MongoReporter()
        reporter._run_id = None
        with mock.patch.object(reporter._db_client, "insert", mock.Mock()) as mock_insert:
            reporter._save_test_run()
        mock_insert.assert_called_once_with(collection_name=MongoReporter._TEST_RUN_COLLECTION_NAME,
                                            document=reporter._mongo_run_document)

    def test_save_test_run_run_id(self):
        reporter = MongoReporter(run_id=ObjectId())
        with mock.patch.object(reporter._db_client, "replace", mock.Mock()) as mock_replace:
            reporter._save_test_run()
        mock_replace.assert_called_once_with(collection_name=MongoReporter._TEST_RUN_COLLECTION_NAME,
                                             document_id=reporter._run_id, new_document=reporter._mongo_run_document)
