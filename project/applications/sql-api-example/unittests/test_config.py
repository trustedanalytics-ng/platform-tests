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

from app.config import VCAP_SERVICES, Config, ConfigurationError


class BaseBindingParseTest(unittest.TestCase):
    expected = {"db_type": "mysql56",
                "db_name": "pfahmmdrjx7hbwcu",
                "db_username": "nyiu2xqkmimo70c0",
                "db_password": "tkbvyryegschgwqk",
                "db_hostname": "10.0.4.4",
                "db_port": 33359}
    binding_json = None

    def setUp(self):
        with file("fixtures/{}.json".format(self.binding_json)) as f:
            os.environ[VCAP_SERVICES] = f.read()

    def tearDown(self):
        del os.environ[VCAP_SERVICES]


class SingleBindingTest(BaseBindingParseTest):
    binding_json = "single_binding"

    def test_should_return_credentials(self):
        config = Config()
        self.assertDictContainsSubset(self.expected, config.__dict__)


class NotOnlyDBBinding(BaseBindingParseTest):
    binding_json = "mysql_and_krb_binding"

    def test_should_return_db_credentials(self):
        config = Config()
        self.assertDictContainsSubset(self.expected, config.__dict__)


class MultipleBindingTest(BaseBindingParseTest):
    binding_json = "multiple_binding"

    def test_should_raise_if_multiple_bindigs(self):
        with self.assertRaises(ConfigurationError):
            Config()


class NoBindingTest(unittest.TestCase):
    def setUp(self):
        if VCAP_SERVICES in os.environ:
            del os.environ[VCAP_SERVICES]

    def test_should_raise_if_no_binding(self):
        with self.assertRaises(ConfigurationError):
            Config()
