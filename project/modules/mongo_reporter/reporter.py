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

from datetime import datetime
import socket

from bson import ObjectId

import config
from .client import DBClient


class TestResultType:
    OTHER = "other"
    REGRESSION = "regression"
    SMOKE = "smoke"


class TestRunType:
    API_SMOKE = "api-smoke"
    API_FUNCTIONAL = "api-functional"


class MongoReporter(object):
    _instance = None

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

    _test_run_collection_name = "test_run"
    _test_result_collection_name = "test_result"

    def __new__(cls, mongo_uri, run_id=None, test_run_type=None):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            if run_id is not None:
                run_id = ObjectId(run_id)
            cls._instance._db_client = DBClient(uri=mongo_uri)
            cls._instance._run_id = run_id
            cls._instance._total_test_counter = 0
            cls._instance._mongo_run_document = {
                "end_date": None,
                "environment": None,
                "environment_version": None,
                "finished": False,
                "log": "",
                "platform_components": [],
                "components": [],
                "result": {cls.PASS: 0, cls.FAIL: 0, cls.SKIPPED: 0},
                "start_date": None,
                "started_by": None,
                "status": cls.PASS,
                "test_count": 0,
                "total_test_count": 0,
                "test_version": config.get_test_version(),
                "test_type": test_run_type,
                "environment_availability": False
            }
            cls._instance._save_test_run()
            cls._instance._log = []
        return cls._instance

    def on_run_start(self, environment, environment_version, infrastructure_type, appstack_version, platform_components,
                     components, environment_availability):
        mongo_run_document = {
            "environment": environment,
            "environment_version": environment_version,
            "infrastructure_type": infrastructure_type,
            "appstack_version": appstack_version,
            "platform_components": platform_components,
            "components": components,
            "start_date": datetime.now(),
            "started_by": socket.gethostname(),
            "test_version": config.get_test_version(),
            "environment_availability": environment_availability
        }
        self._mongo_run_document.update(mongo_run_document)
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
            self._update_status(doc, status, increment_test_count=(report.when == "call"))

        # Also for integrity with Team City:
        if report.failed and report.when == "setup":
            doc, status = self._on_test(report, item, failed_by_setup=True)
            self._update_status(doc, status)

    @staticmethod
    def _test_name_from_report_or_item(report, item):
        return item.obj.__doc__.strip() if item.obj.__doc__ else report.nodeid

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

    def _get_test_type_from_report(self, report):
        test_directory = getattr(report, "fspath", None)
        if test_directory is not None and "test_smoke" in test_directory:
            return TestResultType.SMOKE
        priority = self._priority_from_report(report)
        if priority in ["medium", "high"]:
            return TestResultType.REGRESSION
        return TestResultType.OTHER

    @classmethod
    def test_status_from_report(cls, report):
        if report.passed:
            test_status = cls.PASS
        elif report.failed:
            test_status = cls.FAIL
        elif report.skipped:
            test_status = cls.SKIPPED
        else:
            test_status = cls.UNKNOWN
        return test_status

    def _on_test(self, report, item, log="", failed_by_setup=False):
        status = self.test_status_from_report(report)
        bugs = self._marker_args_from_item(item, "bugs")
        name = self._test_name_from_report_or_item(report, item)
        test_mongo_document = {
            "run_id": self._run_id,
            "name": name if not failed_by_setup else "{}: failed on setup".format(name),
            "duration": report.duration if not failed_by_setup else 0.0,
            "priority": self._priority_from_report(report),
            "components": self._marker_args_from_item(item, "components"),
            "defects": ", ".join(bugs),
            "tags": ", ".join(report.keywords),
            "status": status,
            "stacktrace": self._stacktrace_from_report(report),
            "log": log,
            "test_type": self._get_test_type_from_report(report),
        }
        if not failed_by_setup:
            test_mongo_document.update({"order": self._mongo_run_document["test_count"]})
        return test_mongo_document, status

    def _on_fixture(self, report, item, reason, log=""):
        status = None
        name = self._test_name_from_report_or_item(report, item)
        if reason == "error":
            name = "{}: {} error".format(name, report.when)
            status = self.FAIL
        elif reason == "skipped":
            name = "{}: skipped".format(name)
            status = self.SKIPPED
        fixture_mongo_document = {
            "run_id": self._run_id,
            "name": name,
            "stacktrace": self._stacktrace_from_report(report),
            "components": self._marker_args_from_item(item, "components"),
            "log": log,
            "test_type": self._get_test_type_from_report(report)
        }
        return fixture_mongo_document, status

    def _update_status(self, result_document, test_status, increment_test_count=False):
        self._total_test_counter += 1
        if increment_test_count:
            self._mongo_run_document["test_count"] += 1

        self._db_client.insert(collection_name=self._test_result_collection_name, document=result_document)

        if self._mongo_run_document["status"] == self.PASS and test_status == self.FAIL:
            self._mongo_run_document["status"] = self.FAIL
        self._mongo_run_document["result"][test_status] += 1
        self._save_test_run()

    def _save_test_run(self):
        if self._run_id is None:
            self._run_id = self._db_client.insert(collection_name=self._test_run_collection_name,
                                                  document=self._mongo_run_document)
        else:
            self._db_client.replace(collection_name=self._test_run_collection_name, document_id=self._run_id,
                                    new_document=self._mongo_run_document)
