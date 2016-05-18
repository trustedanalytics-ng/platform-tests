#
# Copyright (c) 2015-2016 Intel Corporation
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

import abc
import json
import time

from bs4 import BeautifulSoup
import requests

from configuration import config
from .exceptions import UnexpectedResponseError
from .tap_logger import log_http_request, log_http_response


class PlatformApiClient(metaclass=abc.ABCMeta):
    """Base class for HTTP clients"""

    _CLIENTS = {"app": {}, "console": {}}

    @abc.abstractmethod
    def __init__(self, platform_username, platform_password):
        self._username = platform_username
        self._password = platform_password
        self._domain = config.CONFIG["domain"]
        self._login_endpoint = "login.{}".format(self._domain)
        self._session = requests.Session()
        self._session.proxies = config.get_proxy()
        self._session.verify = config.CONFIG["ssl_validation"]

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self._username)

    def get_username(self):
        return self._username

    @classmethod
    def get_admin_client(cls, client_type=None):
        admin_username = config.CONFIG["admin_username"]
        admin_password = config.CONFIG["admin_password"]
        return cls.get_client(admin_username, admin_password, client_type)

    @classmethod
    def get_client(cls, username, password=None, client_type=None):
        if client_type is None:
            client_type = config.CONFIG["client_type"]
        if client_type not in ["app", "console"]:
            raise ValueError("invalid client_type")
        if cls._CLIENTS[client_type].get(username) is None:
            if client_type == "console":
                cls._CLIENTS[client_type][username] = ConsoleClient(username, password)
            elif client_type == "app":
                cls._CLIENTS[client_type][username] = AppClient(username, password)
        return cls._CLIENTS[client_type][username]

    def request(self, method, endpoint, headers=None, files=None, params=None, data=None, body=None, log_msg="", auth=None):
        request = requests.Request(
            method=method.upper(),
            url=self.url + endpoint,
            headers=headers,
            data=data,
            params=params,
            json=body,
            files=files,
            auth=auth
        )
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, self._password, description=log_msg, data=data)
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    def download_file(self, endpoint, target_file_path):
        """Download (large) file in chunks and save it to target_file_path."""
        request = requests.Request("GET", url=self.url + endpoint)
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, description="PLATFORM: Download file")
        response = self._session.send(request, stream=True)
        log_http_response(response, logged_body_length=0)  # the body is a long stream of binary data
        with open(target_file_path, 'w+b') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()


class ConsoleClient(PlatformApiClient):
    """HTTP client which calls Platform API - using console endpoint and cookie-based authentication."""

    def __init__(self, platform_username, platform_password=None):
        super().__init__(platform_username, platform_password)
        if platform_password is not None:
            self.authenticate(platform_password)

    @classmethod
    def get_admin_client(cls, client_type=None):
        return super().get_admin_client(client_type="console")

    @property
    def url(self):
        return "https://console.{}/".format(self._domain)

    def create_login_url(self, path):
        return "{}://{}/{}".format(config.CONFIG["login.do_scheme"], self._login_endpoint, path)

    def _get_csrf_data(self):
        csrf_data = {}
        url = self.create_login_url("login")
        response = self.get(url, "authenticate: get login form")
        csrf_code = self._parse_csrf_code(response)
        if csrf_code is not None:
            csrf_data["X-Uaa-Csrf"] = csrf_code
        return csrf_data

    @staticmethod
    def _parse_csrf_code(message):
        soup = BeautifulSoup(message, 'html.parser')
        input = soup.find("input", attrs={"name": "X-Uaa-Csrf"})
        code = None
        if input is not None:
            code = input["value"]
        return code

    def authenticate(self, password):
        data = {"username": self._username, "password": password}
        data.update(self._get_csrf_data())
        request = requests.Request(
            method="POST",
            url=self.create_login_url("login.do"),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, self._password, description="Authenticate user")
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok or "Unable to verify email or password. Please try again." in response.text:
            raise UnexpectedResponseError(response.status_code, response.text)

    def logout(self):
        url = self.create_login_url("logout")
        response = self._session.get(url)
        log_http_response(response)

    def post(self, url, data, description):
        request = requests.Request(
            method="POST",
            url=url,
            data=data,
            headers={"Accept": "text/html", "Content-Type": "application/x-www-form-urlencoded"}
        )
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, description=description)
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)

    def get(self, url, description=""):
        request = self._session.prepare_request(requests.Request("GET", url=url))
        log_http_request(request, self._username, description=description)
        response = self._session.send(request)

        log_http_response(response)

        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        return response.text

    def put(self, url, data, description=""):
        request = requests.Request(
                method="PUT",
                url=url,
                data=data,
                headers={"Accept": "application/json", "Content-Type": "application/json;charset=UTF-8"}
        )
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, description=description)
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)


class AppClient(PlatformApiClient):
    """HTTP client which calls APIs of specific applications (bypassing console) using token-based authentication"""

    _TOKEN_EXPIRY_TIME = 298  # (in seconds) 5 minutes minus 2s buffer
    GUID_PATTERN = "([a-z]|[0-9]|-)*"
    APP_ENDPOINT_MAP = {  # matches application names with API endpoint patterns
        "app-launcher-helper": lambda x: "atkinstances" in x,
        "das": lambda x: x.startswith("rest/das"),
        "data-catalog": lambda x: x.startswith("rest/datasets"),
        "fileserver": lambda x: x.startswith("/files"),
        "hive": lambda x: x.startswith("rest/tables"),
        "latest-events-service": lambda x: x.startswith("rest/les"),
        "metrics-provider": lambda x: "metrics" in x,
        "service-catalog": lambda x: x.startswith("rest/service"),
        "user-management": lambda x: (("orgs" in x and "atkinstances" not in x and "metrics" not in x) or
                                      ("spaces" in x) or ("invitations" in x) or ("registrations" in x)),
        "hdfs-uploader": lambda x: x.startswith("rest/upload")
    }
    LOGIN_TOKEN = "Basic Y2Y6"

    def __init__(self, platform_username, platform_password):
        super().__init__(platform_username, platform_password)
        self._token = None
        self._token_retrieval_time = 0
        self._application_name = None
        if platform_password is not None:
            self._get_token()

    @property
    def url(self):
        return "http://{}.{}/".format(self._application_name, self._domain)

    @classmethod
    def get_admin_client(cls, client_type=None):
        return super().get_admin_client(client_type="app")

    def _get_token(self):
        path = "https://{}/oauth/token".format(self._login_endpoint)
        headers = {
            "Authorization": self.LOGIN_TOKEN,
            "Accept": "application/json"
        }
        data = {"username": self._username, "password": self._password, "grant_type": "password"}
        request = requests.Request("POST", path, data=data, headers=headers)
        request = self._session.prepare_request(request)
        self._token_retrieval_time = time.time()
        log_http_request(request, self._username, self._password, "Retrieve cf token")
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        self._token = "Bearer {}".format(json.loads(response.text)["access_token"])

    def request(self, method, endpoint, headers=None, files=None, params=None, data=None, body=None, log_msg="",
                app_name=None):
        # check whether token has expired
        if (self._token is not None) and (time.time() - self._token_retrieval_time > self._TOKEN_EXPIRY_TIME):
            self._get_token()
        headers = {} if headers is None else headers
        headers["Authorization"] = self._token
        if app_name is not None:
            self._application_name = app_name
        else:
            self._application_name = next((k for k, v in self.APP_ENDPOINT_MAP.items() if v(endpoint)), "")
        return super().request(method, endpoint, headers, files, params, data, body, log_msg)


class CfApiClient(AppClient):
    """HTTP client for CF api calls. Uses token-based authentication."""

    _CF_API_CLIENT = None

    def __init__(self, platform_username, platform_password):
        super().__init__(platform_username, platform_password)

    @property
    def url(self):
        return "https://api.{}/v2/".format(config.CONFIG["domain"])

    @classmethod
    def get_client(cls):
        if cls._CF_API_CLIENT is None:
            admin_username = config.CONFIG["admin_username"]
            admin_password = config.CONFIG["admin_password"]
            cls._CF_API_CLIENT = cls(admin_username, admin_password)
        return cls._CF_API_CLIENT

    def get_oauth_token(self):
        self._get_token()
        return self._token
