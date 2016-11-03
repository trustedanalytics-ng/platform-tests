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

import os
import unittest
import json

from app.config import Config


class BaseBindingParseTest(unittest.TestCase):
    expected_mysql = {"db_type": b"mysql56",
                      "db_name": b"pfahmmdrjx7hbwcu",
                      "db_username": b"nyiu2xqkmimo70c0",
                      "db_password": b"tkbvyryegschgwqk",
                      "db_hostname": b"10.0.4.4",
                      "db_port": 3306}
    binding_json = None
    test_path = os.path.dirname(os.path.realpath(__file__))
    fixture_path = os.path.join(test_path, "fixtures/{}.json")

    def setUp(self):
        with open(self.fixture_path.format(self.binding_json)) as f:
            os.environ = json.loads(f.read())

    def tearDown(self):
        os.environ = {}


class SingleBindingTest(BaseBindingParseTest):
    binding_json = "single_binding"

    def test_should_return_credentials(self):
        config = Config()
        self.assertDictContainsSubset(self.expected_mysql, config.__dict__)


class NotOnlyDBBinding(BaseBindingParseTest):
    binding_json = "mysql_and_krb_binding"

    def test_should_return_db_credentials(self):
        config = Config()
        self.assertDictContainsSubset(self.expected_mysql, config.__dict__)
'''

Test skipped due to not implemented usage of application's environmental variables

class MultipleBindingTest(BaseBindingParseTest):
    binding_json = "multiple_binding"
    with file("fixtures/{}.json".format(binding_json)) as f:
        os.environ = f.read()
    def test_should_raise_if_multiple_bindigs(self):
        with self.assertRaises(ConfigurationError):
            Config()
'''


class NoBindingTest(unittest.TestCase):

    def setUp(self):
        os.environ = {}

    def test_should_raise_if_no_binding(self):
        with self.assertRaises(SystemExit):
            Config()
