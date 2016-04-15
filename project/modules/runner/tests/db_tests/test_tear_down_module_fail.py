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
from modules.constants.test_results import TestResult
from modules.runner.tests.db_tests.base_test import BaseDbTest


class PassingTestCase(BaseDbTest):

    def test_documents(self):
        self.assertResultDocuments(
            TestResult.success, "test_pass", False,
            TestResult.error, "tearDownModule", True
        )
