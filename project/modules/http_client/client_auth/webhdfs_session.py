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
import sys

from requests import Request

from ...tap_logger import log_http_response
from ...constants.http_status import HttpStatus
from ...exceptions import RedirectionLimitException, UnexpectedResponseError
from .http_session import HttpSession

ALLOWED_REDIRECTION_LIMIT = 3


def counted(func):
    def counting_calls(*args, **kwargs):
        counting_calls.calls += 1
        if counting_calls.calls > ALLOWED_REDIRECTION_LIMIT:
            raise RedirectionLimitException("Exceeded allowed redirection number")
        return func(*args, **kwargs)
    counting_calls.calls = 0
    return counting_calls


class WebhdfsSession(HttpSession):

    def _request_perform(self, request: Request, raw_response: bool):
        """Perform request and return response."""
        response = self._session.send(request, allow_redirects=False)
        log_http_response(response)
        if raw_response is True:
            return response
        if response.status_code == HttpStatus.CODE_TEMPORARY_REDIRECT:
            return response
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @staticmethod
    @counted
    def redirection_handler(webhdfs_create, test_port, via_host_username, path_to_key, webhdfs_get_via_hostname,
                            test_host, method, body=None, params=None, redirection_location=None, hdfs_path=""):
        ssh_tunnel = None
        target_host = redirection_location.split("://", 1)[1].split("/", 1)[0]
        target_port = test_port
        if ":" in target_host:
            target_host, target_port = tuple(target_host.split(":"))
            target_port = int(target_port)
        new_params = {"namenoderpcaddress": "nameservice1", "offset": 0}
        params.update(new_params)

        # Dynamic import due to pack.sh remove module issue
        __import__('modules.ssh_client')
        ssh_client = sys.modules['modules.ssh_client']

        try:
            ssh_tunnel = ssh_client.SshTunnel(
                target_host, via_host_username, path_to_key=path_to_key, port=target_port,
                via_hostname=webhdfs_get_via_hostname(), local_port=target_port)
            ssh_tunnel.connect()
            webhdfs = webhdfs_create(host=test_host, port=target_port)
            response = webhdfs.request(method, body=body, params=params, path=hdfs_path)
        except ConnectionError:
            raise ssh_client.SshTunnelException()
        finally:
            ssh_tunnel.disconnect()
        return response
