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

from unittest import TestCase
from unittest.mock import Mock, patch

from configuration.dynamic_config import _DynamicConfig
from modules.constants import TapComponent


class TestDynamicConfig(TestCase):

    @patch("modules.tap_object_model.Application.cf_api_get_list")
    def test_uaa_data_getting_only_once(self, cf_api_get_list):
        client_id = "id"
        client_secret = "secret"
        data = {
            "VCAP_SERVICES": {
                "user-provided": [
                    {"name": "sso", "credentials": {"clientId": client_id, "clientSecret": client_secret}}
                ]
            }
        }
        user_management = Mock()
        user_management.name = TapComponent.user_management.value
        user_management.cf_api_env.return_value = data
        cf_api_get_list.return_value = [user_management]

        dynamic_config = _DynamicConfig()

        expected_uaa_auth = (client_id, client_secret)
        uaa_auth_1 = dynamic_config.get("uaa_auth")
        uaa_auth_2 = dynamic_config.get("uaa_auth")
        self.assertEquals(uaa_auth_1, expected_uaa_auth)
        self.assertEquals(uaa_auth_2, expected_uaa_auth)
        self.assertEquals(user_management.cf_api_env.call_count, 1)
