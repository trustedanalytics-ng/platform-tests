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

import unittest
from unittest.mock import patch


class MockHttpSession(unittest.TestCase):
    """Util class to mock http session responses."""

    def mock_http_session(self):
        """Mock http session request call."""
        self.http_session_response = {
            "access_token": "11-22-33-44",
            "expires_in": 123
        }
        patcher = patch('modules.http_client.client_auth.http_session.HttpSession.request')
        self.mock_http_session_call = patcher.start()
        self.mock_http_session_call.return_value = self.http_session_response
        self.addCleanup(patcher.stop)
