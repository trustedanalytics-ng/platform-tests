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

import socket
from unittest import TestCase, mock

import mongomock

import config
from modules.mongo_reporter import reporter


class MockClient(reporter.DBClient):
    def __init__(self, uri):
        self.database = mongomock.MongoClient().db


class MockPassingReport:
    class Dummy:
        pass
    _priority = "high"
    when = "call"
    duration = 0.123
    passed = True
    failed = False
    nodeid = "passing.test"
    keywords = ("a", "b", "c", "priority_" + _priority)
    longrepr = Dummy()
    test_type = reporter.TestResultType.REGRESSION


class MockPassingItem:
    class MockMarker:
        def __init__(self, *args):
            self.args = args
    _components = ("c", "o", "m", "p")
    _bugs = ("b", "u", "g")
    components = MockMarker(*_components)
    bugs = MockMarker(*_bugs)

    @property
    def obj(self):
        return ""

    @classmethod
    def get_marker(cls, name):
        return getattr(cls, name)


class MockFailingReport:
    class Traceback:
        reprtraceback = "stacktrace"
    _priority = "medium"
    when = "call"
    duration = 0.123
    passed = False
    failed = True
    nodeid = "failing.test"
    keywords = ("priority_" + _priority,)
    longrepr = Traceback()
    test_type = reporter.TestResultType.REGRESSION


class MockFailingSetupReport:
    class Traceback:
        reprtraceback = "stacktrace"
    _priority = "medium"
    when = "setup"
    duration = 0.123
    passed = False
    failed = True
    nodeid = "failing.test"
    keywords = ("priority_" + _priority,)
    longrepr = Traceback()


class MockFailingItem:

    @property
    def obj(self):
        return ""

    @classmethod
    def get_marker(cls, name):
        return getattr(cls, name, None)


class TestReporter(TestCase):

    @mock.patch.object(reporter, "DBClient", MockClient)
    def setUp(self):
        self.mongo_reporter = reporter.MongoReporter(mongo_uri=None, run_id=None,
                                                     test_run_type=reporter.TestRunType.API_FUNCTIONAL)

    def tearDown(self):
        reporter.MongoReporter._instance = None

    def assertRunDocument(self, tested_document, expected_run_document):
        expected_keys = list(expected_run_document.keys()) + ["start_date", "end_date", "_id"]
        self.assertListEqual(sorted(list(tested_document.keys())), sorted(expected_keys))
        for key, val in expected_run_document.items():
            self.assertEqual(tested_document[key], val, "incorrect {}".format(key))
        self.assertIsNotNone(tested_document["start_date"])
        if expected_run_document["finished"]:
            self.assertIsNotNone(tested_document["end_date"])
        else:
            self.assertIsNone(tested_document["end_date"])

    def assertTestDocument(self, tested_document, expected_document):
        expected_keys = list(expected_document.keys()) + ["_id"]
        self.assertListEqual(sorted(list(tested_document.keys())), sorted(expected_keys))
        for key, val in expected_document.items():
            self.assertEqual(tested_document[key], val, "incorrect {}".format(key))

    def get_run_documents(self):
        run_collection = reporter.MongoReporter._test_run_collection_name
        return list(self.mongo_reporter._db_client.database[run_collection].find({}))

    def get_result_documents(self):
        result_collection = reporter.MongoReporter._test_result_collection_name
        return list(self.mongo_reporter._db_client.database[result_collection].find({}))

    def start_run(self):
        expected_run_document = self.get_expected_run_document()
        self.mongo_reporter.on_run_start(
            expected_run_document["environment"],
            expected_run_document["environment_version"],
            expected_run_document["infrastructure_type"],
            expected_run_document["appstack_version"],
            expected_run_document["platform_components"],
            expected_run_document["components"]
        )
        return expected_run_document

    def test_reporter_run(self):
        # on run start
        expected_run_document = self.start_run()
        run_documents = self.get_run_documents()
        result_documents = self.get_result_documents()
        self.assertEqual(len(run_documents), 1)
        self.assertEqual(len(result_documents), 0)
        self.assertRunDocument(run_documents[0], expected_run_document)

        # on run end
        self.mongo_reporter.on_run_end()
        run_documents = self.get_run_documents()
        expected_run_document.update({"finished": True})
        self.assertRunDocument(run_documents[0], expected_run_document)

    def test_reporter_passed_test_case(self):
        # start run
        expected_run_document = self.start_run()
        run_documents = self.get_run_documents()
        run_id = run_documents[0]["_id"]

        # log passed test
        self.mongo_reporter.log_report(MockPassingReport, MockPassingItem)
        run_documents = self.get_run_documents()
        result_documents = self.get_result_documents()
        self.assertEqual(len(run_documents), 1)
        expected_run_document.update({"test_count": 1})
        expected_run_document["result"].update({reporter.MongoReporter.PASS: 1,
                                                reporter.MongoReporter.FAIL: 0,
                                                reporter.MongoReporter.SKIPPED: 0})
        self.assertRunDocument(run_documents[0], expected_run_document)
        self.assertEqual(len(result_documents), 1)
        expected_document = self.get_expected_test_document(
            run_id=run_id, test_name=MockPassingReport.nodeid, duration=MockPassingReport.duration,
            order=0, priority=MockPassingReport._priority, components=tuple(sorted(MockPassingItem._components)),
            defects=tuple(sorted(MockPassingItem._bugs)), tags=MockPassingReport.keywords, stacktrace=None, log="",
            status=reporter.MongoReporter.PASS, test_type=MockPassingReport.test_type
        )
        self.assertTestDocument(result_documents[0], expected_document)

    def test_reporter_failed_test_case(self):
        # start run
        expected_run_document = self.start_run()
        run_documents = self.get_run_documents()
        run_id = run_documents[0]["_id"]

        # log failed test
        self.mongo_reporter.log_report(MockFailingReport, MockFailingItem)
        run_documents = self.get_run_documents()
        result_documents = self.get_result_documents()
        self.assertEqual(len(run_documents), 1)
        expected_run_document.update({"status": reporter.MongoReporter.FAIL, "test_count": 1})
        expected_run_document["result"].update({reporter.MongoReporter.PASS: 0,
                                                reporter.MongoReporter.FAIL: 1,
                                                reporter.MongoReporter.SKIPPED: 0})
        self.assertRunDocument(run_documents[0], expected_run_document)
        self.assertEqual(len(result_documents), 1)
        expected_document = self.get_expected_test_document(
            run_id=run_id, test_name=MockFailingReport.nodeid, duration=MockFailingReport.duration,
            order=0, priority=MockFailingReport._priority, components=tuple(), defects=tuple(),
            tags=MockFailingReport.keywords, stacktrace=MockFailingReport.Traceback.reprtraceback, log="",
            status=reporter.MongoReporter.FAIL, test_type=MockFailingReport.test_type
        )
        self.assertTestDocument(result_documents[0], expected_document)

    def test_should_log_two_results_on_setup_fail(self):
        self.mongo_reporter.log_report(MockFailingSetupReport, MockFailingItem)
        run_documents = self.get_run_documents()
        self.assertEqual(len(run_documents), 1)
        result_documents = self.get_result_documents()
        self.assertEqual(len(result_documents), 2)
        self.assertEqual(run_documents[0]["result"], self.get_expected_run_document(fail_count=2)["result"])

    def get_expected_test_document(self, run_id, test_name, duration, order, priority, components, defects,
                                   tags, status, stacktrace, log, test_type):
        return {
            "run_id": run_id,
            "name": test_name,
            "duration": duration,
            "order": order,
            "priority": priority,
            "components": components,
            "defects": ", ".join(defects),
            "tags": ", ".join(tags),
            "status": status,
            "stacktrace": stacktrace,
            "log": log,
            "test_type": test_type,
        }

    def get_expected_run_document(self, pass_count=0, fail_count=0, skipped_count=0, test_count=0, finished=False,
                                  status="PASS"):
        expected_run = {
            "environment": "test_environment",
            "environment_version": "0.7",
            "infrastructure_type": "AWS",
            "appstack_version": "master",
            "finished": finished,
            "log": "",
            "platform_components": ("a", "b", "c"),
            "components": ["d", "e", "f"],
            "result": {
                reporter.MongoReporter.PASS: pass_count,
                reporter.MongoReporter.FAIL: fail_count,
                reporter.MongoReporter.SKIPPED: skipped_count
            },
            "started_by": socket.gethostname(),
            "status": status,
            "test_count": test_count,
            "test_type": reporter.TestRunType.API_FUNCTIONAL,
            "total_test_count": 0,
            "test_version": config.get_test_version()
        }
        return expected_run
