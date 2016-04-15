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
from modules.runner.tap_test_case import TapTestCase


def setUpModule():
    raise AssertionError()


class PassingTestCase(TapTestCase):
    @classmethod
    def tearDownClass(cls):
        pass

    def test_pass(self):
        self.assertTrue(True)
