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

import abc
import json
import ssl
import uuid
from urllib.parse import urlsplit, urlunsplit
from time import sleep

import config
from ..constants import ServiceLabels, ServicePlan
from ..http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from ..http_client.http_client_factory import HttpClientFactory
from ..tap_logger import get_logger
from ..tap_object_model import ServiceInstance
from ..test_names import generate_test_object_name
from ..websocket_client import WebsocketClient

logger = get_logger(__name__)


def _generate_uuid():
    return str(uuid.uuid4()).replace("-", "")


class JupyterWSBase(metaclass=abc.ABCMeta):
    WS_TIMEOUT = 5  # (seconds) - timeout for unresponsive socket

    def __init__(self, uri, origin, headers, cert_requirement):
        self.ws = WebsocketClient(uri, origin, headers, cert_requirement)

    @abc.abstractmethod
    def _get_command_payload(self, content):
        pass

    def _get_reply_payload(self, content):
        pass

    def send_input(self, content, reply=False, obscure_from_log=False):
        if reply:
            msg = self._get_reply_payload(content)
        else:
            msg = self._get_command_payload(content)
        if obscure_from_log:
            logger.info(msg.replace(content, "[SECRET]"))
        else:
            logger.info(msg)
        self.ws.send(msg)

    def get_output(self):
        """Retrieve all messages"""
        return self.ws.recieve()


class JupyterTerminal(JupyterWSBase):

    def __init__(self, uri, origin, headers, cert_requirement, number):
        super().__init__(uri, origin, headers, cert_requirement)
        self.number = number

    def __repr__(self):
        return "Terminal {}".format(self.number)

    def _get_command_payload(self, msg):
        return json.dumps(["stdin", msg])


class JupyterNotebook(JupyterWSBase):

    def __init__(self, uri, origin, headers, cert_requirement, session_id, path):
        super().__init__(uri, origin, headers, cert_requirement)
        self._session_id = session_id
        self._path = path
        self._last_msg_id = None

    def __repr__(self):
        return "{} (path={}, session_id={})".format(self.__class__.__name__, self._path, self._session_id)

    def _get_command_payload(self, content):
        """Return full message passed as command to Jupyter notebook"""
        self._last_msg_id = _generate_uuid()  # see Jupyter JavaScript static/services/kernels/kernel.js, line 74
        msg = {
            "header": {"msg_id": self._last_msg_id, "username": "username", "session": self._session_id,
                       "msg_type": "execute_request", "version": "5.0"},
            "metadata": {},
            "content": {"code": content, "silent": False, "store_history": True, "user_expressions": {},
                        "allow_stdin": True, "stop_on_error": True},
            "buffers": [],
            "parent_header": {},
            "channel": "shell"
        }
        return json.dumps(msg)

    def _get_reply_payload(self, content):
        """Return full message passed as interactive reply to a prompt"""
        self._last_msg_id = _generate_uuid()  # see Jupyter JavaScript static/services/kernels/kernel.js, line 74
        msg = {
            "header": {"msg_id": self._last_msg_id, "username": "username", "session": self._session_id,
                       "msg_type": "input_reply", "version": "5.0"},
            "metadata": {},
            "content": {"value": content},
            "buffers": [],
            "parent_header": {},
            "channel": "stdin"
        }
        return json.dumps(msg)

    def _get_frames_with_msg_type(self, msg_type):
        output = self.get_output()
        output = [json.loads(item) for item in output]
        return (frame for frame in output if frame["msg_type"] == msg_type)

    def _get_frame_with_msg_type(self, msg_type):
        return next(self._get_frames_with_msg_type(msg_type))

    def get_command_result(self):
        result_frame = self._get_frame_with_msg_type("execute_request")
        content = result_frame["content"]["data"]["text/plain"]
        return content

    def get_stream_result(self):
        stream_frame = self._get_frames_with_msg_type("stream")
        return [frame["content"]["text"] for frame in stream_frame]

    def check_command_status(self):
        reply_frame = self._get_frame_with_msg_type("execute_reply")
        status = reply_frame["content"]["status"]
        if status == "error":
            raise AssertionError("{} {} {}".format(self, reply_frame["content"]["ename"],
                                                   reply_frame["content"]["evalue"]))
        return status

    def get_prompt_text(self):
        reply_frame = self._get_frame_with_msg_type("input_request")
        return reply_frame["content"]["prompt"]


class Jupyter(object):
    """Jupyter service instance."""

    def __init__(self, context, instance_name=None, params=None):
        if instance_name is None:
            instance_name = generate_test_object_name(short=True, prefix=ServiceLabels.JUPYTER)
        self.instance = ServiceInstance.create_with_name(
            context=context,
            name=instance_name,
            offering_label=ServiceLabels.JUPYTER,
            plan_name=ServicePlan.SINGLE_SMALL,
            params=params
        )
        self.instance.ensure_running()
        self.instance_url = self.instance.url
        self.client = HttpClientFactory.get(ConsoleConfigurationProvider.get(url=self.instance.url, rest_prefix=""))
        sleep(300)
        # Visit jupyter main page to start session
        response = self.client.request(
            method=HttpMethod.GET,
            path="",
            msg="Jupyter: main page",
        )

    def __repr__(self):
        return "{} (instance_url={})".format(self.__class__.__name__, self.instance_url)

    @property
    def cookie_header(self):
        cookie_items = ("{}={}".format(k, v) for k,v in self.client.cookies.get_dict().items())
        return "; ".join(cookie_items)

    @property
    def use_ssl(self):
        return self.instance_url.startswith('https')

    @property
    def ws_sslopt(self):
        return self._get_ws_ssl_options() if self.use_ssl else None

    @property
    def ws_scheme(self):
        return WebsocketClient.WSS if self.use_ssl else WebsocketClient.WS

    def connect_to_terminal(self, terminal_no):
        terminal_path = "terminals/websocket/{}".format(terminal_no)
        uri = urlunsplit(urlsplit(self.instance_url)._replace(scheme=self.ws_scheme, path=terminal_path))
        origin = self.instance_url
        headers = {"Cookie": self.cookie_header}
        return JupyterTerminal(uri, origin, headers, self.ws_sslopt, terminal_no)

    def create_notebook(self, python_version=2):
        python_version = "python{}".format(python_version)
        response = self.client.request(
            method=HttpMethod.POST,
            path="api/contents",
            body={"type": "notebook"},
            msg="Jupyter: create notebook"
        )
        notebook_path = response["path"]
        response = self.client.request(
            method=HttpMethod.POST,
            path="api/sessions",
            body={
                "kernel": {"id": None, "name": python_version},
                "notebook": {"path": notebook_path}
            },
            msg="Jupyter: create kernel session for {}".format(python_version)
        )
        kernel_id = response["kernel"]["id"]
        session_id = response["id"]
        channel_path = "api/kernels/{}/channels?session_id={}".format(kernel_id, session_id)
        uri = urlunsplit(urlsplit(self.instance_url)._replace(scheme=self.ws_scheme, path=channel_path))
        origin = self.instance_url
        headers = {"Cookie": self.cookie_header}
        return JupyterNotebook(uri, origin, headers, self.ws_sslopt, session_id, notebook_path)

    def get_notebook_source(self, notebook_path):
        notebook_model = self.client.request(
            method=HttpMethod.GET,
            path="api/contents/{}".format(notebook_path),
            body={"type": "notebook"},
            msg="Jupyter: get source from {}".format(notebook_path)
        )
        cells = notebook_model['content']['cells']
        code_source = [c['source'] for c in cells if c['cell_type'] == "code" and len(c['source']) > 0]
        return code_source

    @staticmethod
    def _get_ws_ssl_options():
        """Get web socket ssl options."""
        options = None
        if not config.ssl_validation:
            options = ssl.CERT_NONE
        return options
