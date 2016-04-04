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

from .client import DBClient


class MongoReporter(object):
    _instance = None

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

    _test_run_collection_name = "test_run"
    _test_result_collection_name = "test_result"

    def __new__(cls, mongo_uri, run_id=None):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance._db_client = DBClient(uri=mongo_uri)
            cls._instance._run_id = run_id
            cls._instance._test_counter = 0
            cls._instance._mongo_run_document = {
                "end_date": None,
                "environment": None,
                "environment_version": None,
                "finished": False,
                "log": "",
                "platform_components": [],
                "result": {cls.PASS: 0, cls.FAIL: 0, cls.SKIPPED: 0},
                "start_date": None,
                "started_by": None,
                "status": cls.PASS,
                "test_count": 0,
                "total_test_count": 0
            }
        return cls._instance

    def on_run_start(self, environment, environment_version, platform_components, tests_to_run_count):
        mongo_run_document = {
            "environment": environment,
            "environment_version": environment_version,
            "platform_components": platform_components,
            "start_date": datetime.now().isoformat(),
            "started_by": socket.gethostname(),
            "total_test_count": tests_to_run_count
        }
        self._mongo_run_document.update(mongo_run_document)
        self._save_test_run()

    def on_run_end(self):
        mongo_run_document = {
            "end_date": datetime.now().isoformat(),
            "finished": True
        }
        self._mongo_run_document.update(mongo_run_document)
        self._save_test_run()

    def log_report(self, report, item):
        if report.when == "call":
            self._on_test_end(
                components=self._marker_args_from_item(item, "components"),
                defects=self._marker_args_from_item(item, "bugs"),
                duration=report.duration,
                log="",
                name=report.nodeid,
                priority=self._priority_from_report(report),
                stacktrace=self._stacktrace_from_report(report),
                status=self.test_status_from_report(report),
                tags=report.keywords
            )
        elif report.failed:
            self._on_fixture_error(
                log="",
                name="{}: {} error".format(report.nodeid, report.when),
                stacktrace=self._stacktrace_from_report(report)
            )

    @staticmethod
    def _marker_args_from_item(item, marker_name):
        args = item.get_marker(marker_name)
        return getattr(args, "args", tuple())

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

    def _on_test_end(self, components: tuple, defects: tuple, duration: float, log: str, name: str, priority: str,
                     stacktrace: str, status: str, tags: tuple):
        mongo_test_document = {
            "run_id": self._run_id,
            "name": name,
            "duration": duration,
            "order": self._test_counter,
            "priority": priority,
            "components": ", ".join(components),
            "defects": ", ".join(defects),
            "tags": ", ".join(tags),
            "status": status,
            "stacktrace": stacktrace,
            "log": log,
        }
        self._db_client.insert(collection_name=self._test_result_collection_name, document=mongo_test_document)
        self._update_run_status(test_status=status)
        self._test_counter += 1

    def _on_fixture_error(self, name: str, stacktrace: str, log: str):
        fixture_mongo_document = {
            "run_id": self._run_id,
            "name": name,
            "stacktrace": stacktrace,
            "log": log
        }
        self._update_run_status(test_status=self.FAIL, increment_test_count=False)
        self._db_client.insert(collection_name=self._test_result_collection_name, document=fixture_mongo_document)

    def _update_run_status(self, test_status, increment_test_count=True):
        if self._mongo_run_document["status"] == self.PASS and test_status == self.FAIL:
            self._mongo_run_document["status"] = self.FAIL
        if increment_test_count:
            self._mongo_run_document["test_count"] += 1
            self._mongo_run_document["result"][test_status] += 1
        self._save_test_run()

    def _save_test_run(self):
        if self._run_id is None:
            self._run_id = self._db_client.insert(collection_name=self._test_run_collection_name,
                                                  document=self._mongo_run_document)
        else:
            self._db_client.replace(collection_name=self._test_run_collection_name,
                                    document_id=self._run_id,
                                    new_document=self._mongo_run_document)
