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
import os
import socket
from datetime import datetime

from bson import ObjectId

import config
from modules.constants import Path
from modules.mongo_reporter.base_reporter import BaseReporter
from modules.tap_logger import get_logger
from ._run_type import RunType
from ._tap_info import TapInfo
from ._teamcity_configuration import TeamCityConfiguration

logger = get_logger(__name__)


class MongoReporter(BaseReporter):

    _TEST_TYPE_SMOKE = "smoke"
    _TEST_TYPE_REGRESSION = "regression"
    _TEST_TYPE_OTHER = "other"

    _TEST_RUN_COLLECTION_NAME = "test_run"
    _TEST_RESULT_COLLECTION_NAME = "test_result"

    def __init__(self, *args, **kwargs):
        stress_run_id = config.stress_run_id
        self._total_test_counter = 0
        mongo_run_document = {
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
            "stress_run_id": stress_run_id,
            "test_count": 0,
            "total_test_count": 0,
            "test_version": self._get_test_version(),
            "teamcity_build_id": TeamCityConfiguration.getint("teamcity.build.id"),
            "teamcity_server_url": TeamCityConfiguration.get("teamcity.serverUrl"),

            # updated in separate methods
            "components": [],
            "environment_availability": True,
            "tap_build_number": None,
            "test_type": None,
        }
        super().__init__(mongo_run_document=mongo_run_document, *args, **kwargs)
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

    def report_tap_build_number(self):
        self._mongo_run_document["tap_build_number"] = TapInfo.get_build_number()
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
            doc, status = self._on_fixture_error(report, item)
        elif report.skipped:
            doc, status = self._on_fixture_skipped(report, item)
        if doc and status:
            return self._update_run_status(doc, status, increment_test_count=(report.when == "call"))

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
        test_mongo_document = self._common_mongo_document(report=report, item=item, log=log)
        name = test_mongo_document["name"]
        test_mongo_document.update({
            "duration": report.duration if not failed_by_setup else 0.0,
            "name": name if not failed_by_setup else "{}: failed on setup".format(name),
            "status": status,
        })
        if not failed_by_setup:
            test_mongo_document.update({"order": self._mongo_run_document["test_count"]})
        return test_mongo_document, status

    def _on_fixture_error(self, report, item, log=""):
        fixture_mongo_document = self._common_mongo_document(report=report, item=item, log=log)
        fixture_mongo_document.update({
            "name": "{}: {} error".format(fixture_mongo_document["name"], report.when),
            "status": self._RESULT_FAIL,
        })
        return fixture_mongo_document, self._RESULT_FAIL

    def _on_fixture_skipped(self, report, item, log=""):
        fixture_mongo_document = self._common_mongo_document(report=report, item=item, log=log)
        fixture_mongo_document.update({
            "name": "{}: skipped".format(fixture_mongo_document["name"]),
            "status": self._RESULT_SKIPPED,
        })
        return fixture_mongo_document, self._RESULT_SKIPPED

    def _common_mongo_document(self, report, item, log):
        name = report.nodeid
        bugs = self._marker_args_from_item(item, "bugs")
        common_mongo_document = {
            "components": self._marker_args_from_item(item, "components"),
            "defects": ", ".join(bugs),
            "docstring": self._get_test_docstring(item),
            "log": log,
            "name": report.nodeid,
            "priority": self._priority_from_report(report),
            "run_id": self._run_id,
            "stacktrace": self._stacktrace_from_report(report),
            "tags": ", ".join(report.keywords),
            "test_type": self._get_test_type_from_report(report),
        }
        return common_mongo_document

    def _update_run_status(self, result_document, test_status, increment_test_count=False):
        self._total_test_counter += 1
        if increment_test_count:
            self._mongo_run_document["test_count"] += 1

        inserted_id = self._db_client.insert(collection_name=self._TEST_RESULT_COLLECTION_NAME, document=result_document)

        if self._mongo_run_document["status"] == self._RESULT_PASS and test_status == self._RESULT_FAIL:
            self._mongo_run_document["status"] = self._RESULT_FAIL
        self._mongo_run_document["result"][test_status] += 1
        self._save_test_run()

        return inserted_id
