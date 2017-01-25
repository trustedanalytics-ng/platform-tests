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

import config
from modules.mongo_reporter.request_reporter import log_request
from modules.tap_logger import log_http_request, log_http_response
from modules.exceptions import UnexpectedResponseError
from .http_method import HttpMethod


class HttpSession(object):
    """User http session."""

    def __init__(self, username: str=None, password: str=None, proxies: dict=None, cert:tuple=None):
        self._username = username
        self._password = password
        self._session = Session()
        if proxies is not None:
            self._session.proxies = proxies
        if cert is not None:
            self._session.cert = cert
        self._session.verify = config.ssl_validation

    @property
    def username(self) -> str:
        """Session user name."""
        return self._username

    @property
    def password(self) -> str:
        """Session user password."""
        return self._password

    @property
    def cookies(self):
        """Session cookies."""
        return self._session.cookies

    def request(self, method: HttpMethod, url, headers=None, files=None,
                data=None, params=None, auth=None, body=None, log_message="",
                raw_response=False, timeout=None, raise_exception=True, log_response_content=True):
        """Perform request and return response."""
        request = self._request_prepare(method, url, headers, files,
                                        data, params, auth, body, log_message)
        return self._request_perform(request, raw_response, timeout=timeout,
                                     raise_exception=raise_exception, log_response_content=log_response_content)

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

    def _request_perform(self, request: Request, raw_response: bool,
                         timeout: int, raise_exception: bool, log_response_content=True):
        """Perform request and return response."""
        response = self._send_request_and_get_raw_response(request, timeout=timeout)
        if log_response_content:  # workaround for downloading large files - reading response.text takes too long
            log_http_response(response)
        else:
            log_http_response(response, logged_body_length=0)

        if raise_exception and not response.ok and "session_expired" != response.text.strip():
            raise UnexpectedResponseError(response.status_code, response.text)

        if raw_response is True:
            return response

        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @log_request
    def _send_request_and_get_raw_response(self, request: Request, timeout: int):
        return self._session.send(request, timeout=timeout)
