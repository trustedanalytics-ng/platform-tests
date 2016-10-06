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

from .client_auth.http_method import HttpMethod
from .client_auth.client_auth_base import ClientAuthBase


class HttpClient(object):
    """Http api client."""

    def __init__(self, url: str, auth: ClientAuthBase):
        self.url = url
        self._auth = auth

    @property
    def auth(self):
        """Client auth."""
        return self._auth

    @property
    def cookies(self):
        """Session cookies."""
        return self.auth.session.cookies

    @property
    def session(self):
        return self._auth.session

    @session.setter
    def session(self, session):
        self._auth.session = session

    def request(self, *, method: HttpMethod, url=None, path, headers=None, files=None, params=None, data=None, body=None, msg="",
                raw_response=False, timeout=900, raise_exception=True):
        """Perform request and return response."""
        if not self._auth.authenticated:
            self._auth.authenticate()
        url = self.url if url is None else url
        return self._auth.session.request(
            method=method,
            url="{}/{}".format(url, path),
            headers=headers,
            files=files,
            params=params,
            data=data,
            body=body,
            auth=self._auth.http_auth,
            log_message=msg,
            raw_response=raw_response,
            timeout=timeout,
            raise_exception=raise_exception
        )
