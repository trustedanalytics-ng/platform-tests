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

from requests.auth import AuthBase
from bs4 import BeautifulSoup

from .client_auth_base import ClientAuthBase
from modules.exceptions import UnexpectedResponseError
from modules.http_client.client_auth.http_method import HttpMethod


class ClientAuthLoginPage(ClientAuthBase):
    """Login page based http client authentication."""

    def authenticate(self) -> AuthBase:
        """Use session credentials to authenticate."""
        response = self.session.request(
            method=HttpMethod.POST,
            url="{}/login.do".format(self._url),
            data=self._request_data(),
            headers=self._request_headers(),
            log_message="Authenticate user",
            raw_response=True
        )
        if not response.ok or "Unable to verify email or password. Please try again." in response.text:
            raise UnexpectedResponseError(response.status_code, response.text)

    @property
    def authenticated(self) -> bool:
        return True

    @staticmethod
    def _request_headers():
        """Prepare request data."""
        return {
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _request_data(self):
        """Prepare request data."""
        data = {
            "username": self.session.username,
            "password": self.session.password,
        }
        data.update(self._get_csrf_token_data())
        return data

    def _get_csrf_token_data(self):
        """Prepare data with csrf token."""
        response = self.session.request(
            method=HttpMethod.GET,
            url="{}/login".format(self._url),
            log_message="Authenticate: get login form"
        )
        token = self._get_csrf_token(response)
        data = {}
        if token is not None:
            data["X-Uaa-Csrf"] = token
        return data

    @staticmethod
    def _get_csrf_token(content):
        """Get csrf token from login page html response."""
        soup = BeautifulSoup(content, 'html.parser')
        input_tag = soup.find("input", attrs={"name": "X-Uaa-Csrf"})
        token = None
        if input_tag is not None:
            token = input_tag["value"]
        return token
