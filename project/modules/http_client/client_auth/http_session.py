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

from requests import Session, Request

from configuration import config
from ...tap_logger import log_http_request, log_http_response
from ...exceptions import UnexpectedResponseError
from .http_method import HttpMethod


class HttpSession(object):
    """User http session."""

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._session = self._create_session()

    @property
    def username(self) -> str:
        """Session user name."""
        return self._username

    @property
    def password(self) -> str:
        """Session user password."""
        return self._password

    def request(self, method: HttpMethod, url, headers=None, files=None, data=None, params=None, auth=None, body=None,
                log_message=""):
        """Perform request and return response."""
        request = self._request_prepare(method, url, headers, files, data, params, auth, body, log_message)
        return self._request_perform(request)

    def _request_prepare(self, method, url, headers, files, data, params, auth, body, log_message):
        """Prepare request to perform."""
        request = Request(
            method=method,
            url=url,
            headers=headers,
            files=files,
            data=data,
            params=params,
            auth=auth,
            json=body
        )
        prepared_request = self._session.prepare_request(request)
        log_http_request(prepared_request, self._username, self._password, description=log_message, data=data)
        return prepared_request

    def _request_perform(self, request: Request):
        """Perform request and return response."""
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @staticmethod
    def _create_session():
        """Create http session."""
        session = Session()
        session.verify = config.CONFIG["ssl_validation"]
        return session
