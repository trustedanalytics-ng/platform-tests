#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unittest

from modules.http_client.client_auth.http_session import HttpSession
from modules.http_client.client_auth.client_auth_no_auth import ClientAuthNoAuth


class TestAuthNoAuth(unittest.TestCase):
    """Unit: ClientAuthNoAuth"""

    URL = "test.url"

    def test_init(self):
        auth = ClientAuthNoAuth(url=self.URL, session=HttpSession("username", "password"))
        self.assertIsInstance(auth, ClientAuthNoAuth, "Invalid auth class.")
        self.assertEquals(self.URL, auth._url)
        self.assertTrue(auth.authenticated)

if __name__ == '__main__':
    unittest.main()
