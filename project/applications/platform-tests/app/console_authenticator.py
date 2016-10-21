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

import logging

import bs4
import requests

logger = logging.getLogger(__name__)


class AuthenticationException(Exception):
    pass


class ConsoleAuthenticator(object):
    csrf_data_key = "X-Uaa-Csrf"

    def __init__(self, tap_domain):
        self._login_url = "http://uaa.{}/login.do".format(tap_domain)

    def _get_csrf_token(self, response):
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        input = soup.find("input", attrs={"name": self.csrf_data_key})
        token = None
        if input is not None:
            token = input["value"]
        return token

    def _get_csrf_data(self, session):
        request = requests.Request(method="GET", url=self._login_url)
        request = session.prepare_request(request)
        self._log_request(request)
        response = session.send(request)
        self._log_response(response)
        token = self._get_csrf_token(response)
        data = {}
        if token is not None:
            data[self.csrf_data_key] = token
        return data

    @staticmethod
    def _log_request(prepared_request):
        msg = [
            "--------------- Request ---------------",
            "{} {}".format(prepared_request.method, prepared_request.url)
        ]
        if prepared_request.headers is not None:
            msg.append("headers: {}".format(prepared_request.headers))
        if prepared_request.body is not None:
            msg.append("body: ".format(prepared_request.body))
        logger.info("\n".join(msg))

    @staticmethod
    def _log_response(response):
        msg = [
            "--------------- Response ---------------",
            "Status code: {}".format(response.status_code),
            "Headers: {}".format(response.headers),
            "Text: {}".format(response.text)
        ]
        logger.info("\n".join(msg))

    def authenticate(self, username, password):
        session = requests.session()
        session.verify = False
        data = {"username": username, "password": password}
        data.update(self._get_csrf_data(session))
        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        request = requests.Request(method="POST", url=self._login_url, headers=headers, data=data)
        request = session.prepare_request(request)
        self._log_request(request)
        response = session.send(request)
        self._log_response(response)
        if not response.ok or "forgot_password" in response.text:
            raise AuthenticationException("Authentication failed with credentials: {} {}".format(username, password))
