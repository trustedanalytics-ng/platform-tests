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

import configparser
from datetime import datetime
import os
import socket

from bson import ObjectId

import config
from modules.constants import Path
from modules.tap_logger import get_logger
from ._client import DBClient
from ._teamcity_configuration import TeamCityConfiguration
from ._run_type import RunType

logger = get_logger(__name__)


class _MockDbClient(object):
    """Used when database url is not configured"""
    def __init__(self, *args, **kwargs): pass
    def insert(self, *args, **kwargs): pass
    def replace(self, *args, **kwarg): pass


class MongoReporter(object):

    _RESULT_PASS = "PASS"
    _RESULT_FAIL = "FAIL"
    _RESULT_SKIPPED = "SKIPPED"
    _RESULT_UNKNOWN = "UNKNOWN"

    _TEST_TYPE_SMOKE = "smoke"
    _TEST_TYPE_REGRESSION = "regression"
    _TEST_TYPE_OTHER = "other"

    _TEST_RUN_COLLECTION_NAME = "test_run"
    _TEST_RESULT_COLLECTION_NAME = "test_result"

    def __init__(self, run_id=None):
        if config.database_url is None:
            logger.warning("Not writing results to a database - database_url not configured.")
            self._db_client = _MockDbClient()
        else:
            self._db_client = DBClient(uri=config.database_url)
        if run_id is not None:
            run_id = ObjectId(run_id)
        self._run_id = run_id
        self._total_test_counter = 0
        self._mongo_run_document = {
            "appstack_version": config.appstack_version,  # TODO is it still needed in TAP 0.8?
            "end_date": None,
            "environment": config.tap_domain,
            "environment_version": config.tap_version,
            "finished": False,
            "infrastructure_type": config.tap_infrastructure_type,
            "kerberos": config.kerberos,
            "log": "",
            "parameters": {
                "configuration_parameters": TeamCityConfiguration.get_all(),
                "environment_variables": os.environ,
            },
            "platform_components": [],
            "result": {self._RESULT_PASS: 0, self._RESULT_FAIL: 0, self._RESULT_SKIPPED: 0,
                       self._RESULT_UNKNOWN: 0},
            "start_date": datetime.now(),
            "started_by": socket.gethostname(),
            "status": self._RESULT_PASS,
            "test_count": 0,
            "total_test_count": 0,
            "test_version": self._get_test_version(),
            "teamcity_build_id": TeamCityConfiguration.getint("teamcity.build.id"),
            "teamcity_server_url": TeamCityConfiguration.get("teamcity.serverUrl"),

            # updated in separate methods
            "components": [],
            "environment_availability": True,
            "test_type": None,
        }
        self._save_test_run()
        self._log = []

    def report_components(self, all_test_components):
        self._mongo_run_document["components"] = list(set(all_test_components))
        self._save_test_run()

    def report_test_type(self, pytest_directory_or_file):
        self._mongo_run_document["test_type"] = RunType.get(pytest_directory_or_file)
        self._save_test_run()

    def report_unavailable_environment(self):
        self._mongo_run_document["environment_availability"] = False
        self.on_run_end()
        self._save_test_run()

    def on_run_end(self):
        mongo_run_document = {
            "end_date": datetime.now(),
            "total_test_count": self._total_test_counter,
            "finished": True
        }
        self._mongo_run_document.update(mongo_run_document)
        self._save_test_run()

    def log_report(self, report, item):
        doc, status = None, None
        if report.when == "call":
            doc, status = self._on_test(report, item)
        elif report.failed:
            doc, status = self._on_fixture(report, item, reason="error")
        elif report.skipped:
            doc, status = self._on_fixture(report, item, reason="skipped")
        if doc and status:
            self._update_run_status(doc, status, increment_test_count=(report.when == "call"))

        # Also for consistency with TeamCity:
        if report.failed and report.when == "setup":
            doc, status = self._on_test(report, item, failed_by_setup=True)
            self._update_run_status(doc, status)

    @staticmethod
    def _get_test_version():
        bumpversion_file_path = Path.bumpversion_file
        assert os.path.isfile(bumpversion_file_path), "No such file {}".format(bumpversion_file_path)
        bumpversion_config = configparser.ConfigParser()
        bumpversion_config.read(Path.bumpversion_file)
        version = bumpversion_config["bumpversion"].get("current_version", None)
        assert version is not None, "Version not found in {}".format(bumpversion_file_path)
        return version

    @staticmethod
    def _get_test_docstring(item):
        docstring = item.obj.__doc__
        if docstring:
            docstring = docstring.strip()
        return docstring

    @staticmethod
    def _marker_args_from_item(item, marker_name):
        args = item.get_marker(marker_name)
        return tuple(sorted(set(getattr(args, "args", tuple()))))

    @staticmethod
    def _priority_from_report(report):
        priority_pattern = "priority_"
        for keyword in report.keywords:
            if keyword.startswith(priority_pattern):
                return keyword.replace(priority_pattern, "")

    @staticmethod
    def _stacktrace_from_report(report):
        stacktrace = getattr(report.longrepr, "reprtraceback", None)
        if stacktrace is not None:
            return str(stacktrace)

    @classmethod
    def _get_test_type_from_report(cls, report):
        test_directory = getattr(report, "fspath", None)
        if test_directory is not None and "test_smoke" in test_directory:
            return cls._TEST_TYPE_SMOKE
        priority = cls._priority_from_report(report)
        if priority in ["medium", "high"]:
            return cls._TEST_TYPE_REGRESSION
        return cls._TEST_TYPE_OTHER

    @classmethod
    def _test_status_from_report(cls, report):
        if report.passed:
            test_status = cls._RESULT_PASS
        elif report.failed:
            test_status = cls._RESULT_FAIL
        elif report.skipped:
            test_status = cls._RESULT_SKIPPED
        else:
            test_status = cls._RESULT_UNKNOWN
        return test_status

    def _on_test(self, report, item, log="", failed_by_setup=False):
        status = self._test_status_from_report(report)
        bugs = self._marker_args_from_item(item, "bugs")
        name = report.nodeid
        test_mongo_document = {
            "components": self._marker_args_from_item(item, "components"),
            "defects": ", ".join(bugs),
            "docstring": self._get_test_docstring(item),
            "duration": report.duration if not failed_by_setup else 0.0,
            "log": log,
            "name": name if not failed_by_setup else "{}: failed on setup".format(name),
            "priority": self._priority_from_report(report),
            "run_id": self._run_id,
            "stacktrace": self._stacktrace_from_report(report),
            "status": status,
            "tags": ", ".join(report.keywords),
            "test_type": self._get_test_type_from_report(report),
        }
        if not failed_by_setup:
            test_mongo_document.update({"order": self._mongo_run_document["test_count"]})
        return test_mongo_document, status

    def _on_fixture(self, report, item, reason, log=""):
        status = None
        name = report.nodeid
        if reason == "error":
            name = "{}: {} error".format(name, report.when)
            status = self._RESULT_FAIL
        elif reason == "skipped":
            name = "{}: skipped".format(name)
            status = self._RESULT_SKIPPED
        fixture_mongo_document = {
            "components": self._marker_args_from_item(item, "components"),
            "docstring": self._get_test_docstring(item),
            "log": log,
            "name": name,
            "run_id": self._run_id,
            "stacktrace": self._stacktrace_from_report(report),
            "test_type": self._get_test_type_from_report(report)
        }
        return fixture_mongo_document, status

    def _update_run_status(self, result_document, test_status, increment_test_count=False):
        self._total_test_counter += 1
        if increment_test_count:
            self._mongo_run_document["test_count"] += 1

        self._db_client.insert(collection_name=self._TEST_RESULT_COLLECTION_NAME, document=result_document)

        if self._mongo_run_document["status"] == self._RESULT_PASS and test_status == self._RESULT_FAIL:
            self._mongo_run_document["status"] = self._RESULT_FAIL
        self._mongo_run_document["result"][test_status] += 1
        self._save_test_run()

    def _save_test_run(self):
        if self._run_id is None:
            self._run_id = self._db_client.insert(collection_name=self._TEST_RUN_COLLECTION_NAME,
                                                  document=self._mongo_run_document)
        else:
            self._db_client.replace(collection_name=self._TEST_RUN_COLLECTION_NAME, document_id=self._run_id,
                                    new_document=self._mongo_run_document)
