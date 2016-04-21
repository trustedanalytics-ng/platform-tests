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

import json
import os

from bson.objectid import ObjectId


def set_environment_for_config():
    os.environ["VCAP_APPLICATION"] = json.dumps({"uris": ["dummy.gotapaas.eu"]})


def get_example_run_document(status="pass", end_date="2016-04-01T15:42:01.971197", interrupted=False):
    result = {
        "_id": ObjectId(),
        "environment_version": None,
        "end_date": end_date,
        "log": None,
        "test_count": 20,
        "total_test_count": 20,
        "environment": "daily-nokrb.gotapaas.eu",
        "suite": "test_xxx",
        "release": None,
        "platform_components": [],
        "result": {"error": 7, "fail": 5, "unexpected_success": 1, "expected_failure": 1, "skip": 1, "pass": 11},
        "started_by": "pontus",
        "status": status,
        "start_date": "2016-04-01T15:42:01.778283"
    }
    if interrupted:
        result["interrupted"] = True
    return result

def get_example_test_document(run_id, status="pass"):
    result = {
        "_id": ObjectId(),
        "order": 5,
        "main_component": None,
        "name": "test_xxx.test_yyy.test_test.FailingIncremental.test_1_fail",
        "components": [],
        "log": None,
        "tags": [],
        "reason_skipped": None,
        "priority": "medium",
        "sub_tests": [],
        "status": status,
        "run_id": run_id,
        "description": None,
        "duration": 0.002,
        "suite": "test_xxx",
        "defects": []
    }
    if status != "pass":
        result["stacktrace"] = "abc"
    return result
