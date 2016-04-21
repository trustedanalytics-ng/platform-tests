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
from unittest import mock

from bson.objectid import ObjectId
import mongomock

from . import common

common.set_environment_for_config()
from app.runner import Runner


@mock.patch("runner.TestSuiteModel._collection", mongomock.MongoClient().db.collection)
def test_runner_run_successful_command():
    with mock.patch.object(Runner, "command") as mock_command:
        mock_command.__get__ = mock.Mock(return_value=["pwd"])
        suite = Runner().run("username", "password")
        assert isinstance(suite.id, ObjectId)
        assert suite.is_interrupted() is False


@mock.patch("runner.TestSuiteModel._collection", mongomock.MongoClient().db.collection)
def test_runner_run_unsuccessful_command():
    with mock.patch.object(Runner, "command") as mock_command:
        mock_command.__get__ = mock.Mock(return_value=["python", "-c", "[][0]"])
        runner = Runner()
        suite = runner.run("username", "password")
        wait_until_runner_is_not_busy(runner)
        time.sleep(2)
        assert suite.is_interrupted()

mock_collection = mongomock.MongoClient().db.collection
@mock.patch("runner.TestSuiteModel._collection", mock_collection)
def test_runner_run_non_existing_command():
    with mock.patch.object(Runner, "command") as mock_command:
        mock_command.__get__ = mock.Mock(return_value=["idontexist"])
        runner = Runner()
        suite = runner.run("username", "password")
        wait_until_runner_is_not_busy(runner)
        time.sleep(3)
        assert suite.is_interrupted()


@mock.patch("runner.TestSuiteModel._collection", mongomock.MongoClient().db.collection)
def test_runner_reports_it_is_busy():
    sleep_time = 3
    with mock.patch.object(Runner, "command") as mock_command:
        mock_command.__get__ = mock.Mock(return_value=["sleep", str(sleep_time)])
        runner = Runner()
        runner.run("username", "password")
        assert runner.is_busy
        time.sleep(sleep_time + 1)
        assert not runner.is_busy


def wait_until_runner_is_not_busy(runner, timeout=3):
    start = time.time()
    while time.time() - start < timeout:
        if not runner.is_busy:
            break
        time.sleep(1)
