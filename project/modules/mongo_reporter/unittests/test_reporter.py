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
import os
import socket
from datetime import datetime
from unittest import mock
from unittest.mock import call

import pytest
from bson import ObjectId

from modules.constants import Path
from modules.mongo_reporter._client import MockDbClient
from modules.mongo_reporter.base_reporter import BaseReporter
from modules.mongo_reporter.performance_reporter import PerformanceReporter
from modules.mongo_reporter.reporter import MongoReporter

MOCK_BUMPVERSION_PATH = os.path.join("modules", "mongo_reporter", "unittests", "fixtures", "mock_bumpversion")
assert os.path.isfile(MOCK_BUMPVERSION_PATH)
MOCK_BUMPVERSION_BAD_PATH = os.path.join("modules", "mongo_reporter", "unittests", "fixtures", "mock_bumpversion_bad")
assert os.path.isfile(MOCK_BUMPVERSION_BAD_PATH)

TEST_RUN_ID = ObjectId()


class MockClient:
    def __init__(self, *args, **kwargs): pass
    insert = mock.Mock(return_value=TEST_RUN_ID)
    replace = mock.MagicMock(return_value=None)


class MockConfig:
    appstack_version = "test_appstack_version"
    database_url = "test_uri"
    tap_domain = "test_tap_domain"
    tap_infrastructure_type = "test_infrastructure_type"
    tap_version = "test_tap_version"
    kerberos = "test_kerberos"
    stress_run_id = ObjectId()
    hatch_rate = "test_hatch_rate"
    num_clients = "test_num_clients"


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


TEST_COLLECTION_NAME = "test_collection"


@mock.patch("modules.mongo_reporter.base_reporter.DBClient", MockClient)
class TestBaseReporter(object):
    MockRunDocument = {"test_key": "test_value"}

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    @mock.patch("modules.mongo_reporter.base_reporter.config.database_url", "test_uri")
    def test_init_run_id_is_set(self):
        reporter = BaseReporter(self.MockRunDocument)
        assert reporter._run_id == TEST_RUN_ID

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    @mock.patch("modules.mongo_reporter.base_reporter.config.database_url", "test_uri")
    def test_init_database_url_set(self):
        reporter = BaseReporter(self.MockRunDocument)
        assert isinstance(reporter._db_client, MockClient)

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    @mock.patch("modules.mongo_reporter.base_reporter.config.database_url", None)
    def test_init_no_database_url(self):
        reporter = BaseReporter(self.MockRunDocument)
        assert isinstance(reporter._db_client, MockDbClient)

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    def test_init_run_id(self):
        run_id = ObjectId()
        reporter = BaseReporter(self.MockRunDocument, run_id=run_id)
        assert reporter._run_id == run_id

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    @mock.patch("modules.mongo_reporter.base_reporter.config.database_url", "test_uri")
    @mock.patch.object(BaseReporter, "_save_test_run")
    def test_init_save_run_document(self, mock_method):
        BaseReporter(self.MockRunDocument)
        mock_method.assert_any_call()

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    def test_mongo_run_document(self):
        reporter = BaseReporter(self.MockRunDocument)
        assert reporter._mongo_run_document == self.MockRunDocument

    @mock.patch("modules.mongo_reporter.base_reporter.BaseReporter._TEST_RUN_COLLECTION_NAME", TEST_COLLECTION_NAME)
    @mock.patch("modules.mongo_reporter.base_reporter.config.database_url", "test_uri")
    def test_save_test_run(self):
        run_id = ObjectId()
        reporter = BaseReporter(self.MockRunDocument, run_id=run_id)
        expected_args = {'new_document': {'test_key': 'test_value'}, 'document_id': run_id,
                         'collection_name': TEST_COLLECTION_NAME}
        reporter._db_client.replace.assert_called_with(**expected_args)

    @mock.patch("modules.mongo_reporter.base_reporter.config.database_url", "test_uri")
    def test_cannot_save_run_document_without_name(self):
        with pytest.raises(AssertionError):
            BaseReporter(self.MockRunDocument)


@mock.patch("modules.mongo_reporter.base_reporter.DBClient", MockClient)
class TestPerformanceReporter(object):
    MockStats = None
    StatsPassed = {"stats": [{"num_failures": 0}]}
    StatsFailed = {"stats": [{"num_failures": 1}]}

    @mock.patch("modules.mongo_reporter.performance_reporter.config", MockConfig)
    def test_init_run_document(self):
        run_document = PerformanceReporter()._mongo_run_document
        assert run_document["end_date"] is None
        assert run_document["environment"] == MockConfig.tap_domain
        assert run_document["environment_version"] == MockConfig.tap_version
        assert run_document["finished"] is False
        assert run_document["hatch_rate"] == MockConfig.hatch_rate
        assert run_document["infrastructure_type"] == MockConfig.tap_infrastructure_type
        assert run_document["number_of_users"] == MockConfig.num_clients
        _assert_date_close_enough_to_now(run_document["start_date"])
        assert run_document["started by"] == socket.gethostname()
        assert run_document["status"] == BaseReporter._RESULT_UNKNOWN

    @mock.patch("modules.mongo_reporter.performance_reporter.PerformanceReporter._get_status",
                lambda *args, **kwargs: BaseReporter._RESULT_PASS)
    def test_on_run_end(self):
        reporter = PerformanceReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter.on_run_end(self.MockStats)
        document_after = reporter._mongo_run_document
        _assert_all_keys_equal_except(document_before, document_after, "end_date", "finished", "status")
        _assert_date_close_enough_to_now(document_after["start_date"])
        assert document_after["status"] is BaseReporter._RESULT_PASS
        assert document_after["finished"] is True

    @pytest.mark.parametrize("mock_stats, result", ((StatsPassed, BaseReporter._RESULT_PASS),
                                                    (StatsFailed, BaseReporter._RESULT_FAIL)))
    def test_get_stats(self, mock_stats, result):
        assert PerformanceReporter._get_status(mock_stats) == result

    def test_collection_name_is_not_none(self):
        reporter = PerformanceReporter()
        assert reporter._TEST_RUN_COLLECTION_NAME is not None


@mock.patch("modules.mongo_reporter.base_reporter.DBClient", MockClient)
@mock.patch("modules.mongo_reporter.reporter.TeamCityConfiguration", MockTeamcityConfiguration)
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

    @mock.patch("modules.mongo_reporter.reporter.config", MockConfig)
    def test_init_run_document(self):
        TEST_VERSION = "test.version"
        with mock.patch("modules.mongo_reporter.reporter.MongoReporter._get_test_version",
                        lambda *args, **kwargs: TEST_VERSION):
            run_document = MongoReporter()._mongo_run_document

        # values from config
        assert run_document["appstack_version"] == MockConfig.appstack_version
        assert run_document["environment"] == MockConfig.tap_domain
        assert run_document["environment_version"] == MockConfig.tap_version
        assert run_document["infrastructure_type"] == MockConfig.tap_infrastructure_type
        assert run_document["kerberos"] == MockConfig.kerberos
        assert run_document["stress_run_id"] == MockConfig.stress_run_id
        # values from TeamCityConfiguration
        assert run_document["parameters"]["configuration_parameters"] == MockTeamcityConfiguration.GET_ALL_VALUE
        assert run_document["teamcity_build_id"] == MockTeamcityConfiguration.GETINT_VALUE
        assert run_document["teamcity_server_url"] == MockTeamcityConfiguration.GET_VALUE
        # other dynamic values
        _assert_date_close_enough_to_now(run_document["start_date"])
        assert run_document["started_by"] == socket.gethostname()
        assert run_document["test_version"] == TEST_VERSION
        assert run_document["parameters"]["environment_variables"] == os.environ
        assert run_document["tap_build_number"] is None
        # non-dynamic values
        _assert_date_close_enough_to_now(run_document["start_date"])
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

    def test_report_components(self):
        TEST_COMPONENTS = ["a", "b", "c"]
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter.report_components(TEST_COMPONENTS)
        document_after = reporter._mongo_run_document
        _assert_all_keys_equal_except(document_before, document_after, "components")
        assert sorted(document_after["components"]) == sorted(TEST_COMPONENTS)

    def test_report_test_type(self):
        RUN_TYPE_GET_VALUE = "test-type"
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        with mock.patch("modules.mongo_reporter.reporter.RunType.get", lambda *args, **kwargs: RUN_TYPE_GET_VALUE):
            reporter.report_test_type("xxx")
        document_after = reporter._mongo_run_document
        _assert_all_keys_equal_except(document_before, document_after, "test_type")
        assert reporter._mongo_run_document["test_type"] == RUN_TYPE_GET_VALUE

    def test_report_unavailable_environment(self):
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter.report_unavailable_environment()
        document_after = reporter._mongo_run_document
        _assert_all_keys_equal_except(document_before, document_after, "environment_availability", "end_date",
                                           "finished")
        assert document_after["environment_availability"] is False
        _assert_date_close_enough_to_now(document_after["end_date"])
        assert document_after["finished"] is True

    def test_on_run_end(self):
        TEST_COUNT = 123
        reporter = MongoReporter()
        document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter._total_test_counter = TEST_COUNT
        reporter.on_run_end()
        document_after = reporter._mongo_run_document
        _assert_all_keys_equal_except(document_before, document_after, "end_date", "total_test_count", "finished")
        _assert_date_close_enough_to_now(document_after["start_date"])
        assert document_after["total_test_count"] == TEST_COUNT
        assert document_after["finished"] is True

    @mock.patch("modules.mongo_reporter.reporter.Path.bumpversion_file", MOCK_BUMPVERSION_PATH)
    def test_get_test_version(self):
        version = MongoReporter._get_test_version()
        assert version == "test.version"

    @mock.patch("modules.mongo_reporter.reporter.Path.bumpversion_file", "idontexist")
    def test_get_test_version_missing_bumpversion_file(self):
        with pytest.raises(AssertionError) as e:
            MongoReporter._get_test_version()
        assert "No such file" in e.value.msg

    @mock.patch("modules.mongo_reporter.reporter.Path.bumpversion_file", MOCK_BUMPVERSION_BAD_PATH)
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
        with mock.patch("modules.mongo_reporter.reporter.MongoReporter._priority_from_report",
                        lambda *args, **kwargs: "kitten"):
            test_type = MongoReporter._get_test_type_from_report(report)
        assert test_type == MongoReporter._TEST_TYPE_OTHER

    @pytest.mark.parametrize("priority,expected_test_type", [("medium", MongoReporter._TEST_TYPE_REGRESSION),
                                                             ("high", MongoReporter._TEST_TYPE_REGRESSION),
                                                             ("low", MongoReporter._TEST_TYPE_OTHER),
                                                             ("kitten", MongoReporter._TEST_TYPE_OTHER)])
    def test_type_from_report_priority(self, priority, expected_test_type, dummy_class):
        with mock.patch("modules.mongo_reporter.reporter.MongoReporter._priority_from_report",
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
        _assert_all_keys_equal_except(run_document_before, run_document_after, "status", "result", "test_count")
        assert run_document_after["status"] == expected_run_status
        assert run_document_after["result"][test_status] == run_document_before["result"][test_status] + 1

    @pytest.mark.parametrize("increment_test_count", (True, False))
    def test_update_run_status_increment_test_count(self, increment_test_count):
        reporter = MongoReporter()
        run_document_before = copy.deepcopy(reporter._mongo_run_document)
        reporter._update_run_status(result_document={}, test_status=MongoReporter._RESULT_PASS,
                                    increment_test_count=increment_test_count)
        run_document_after = reporter._mongo_run_document
        _assert_all_keys_equal_except(run_document_before, run_document_after, "result", "test_count")
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

    def test_collection_name_is_not_none(self):
        reporter = MongoReporter()
        assert reporter._TEST_RUN_COLLECTION_NAME is not None


def _assert_date_close_enough_to_now(date, epsilon=0.1):
    assert abs(date - datetime.now()).total_seconds() < epsilon


def _assert_all_keys_equal_except(document_a: dict, document_b: dict, *args):
    for k, v in document_a.items():
        if k not in args:
            assert v == document_b[k], "Value of {} key changed".format(k)
