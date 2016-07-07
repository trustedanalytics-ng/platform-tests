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

import signal

from retry import retry
import websocket

from configuration import config
from modules.constants import ServiceLabels, ServicePlan
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_type import HttpClientType
from modules.tap_logger import get_logger
from modules.tap_object_model import ServiceInstance


logger = get_logger(__name__)


class Seahorse:
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]
    SESSIONS_PATH = "/v1/sessions"
    WORKFLOWS_PATH = "/v1/workflows"

    def __init__(self, org_uuid, space_uuid, tap_http_client):
        self.service_instance = ServiceInstance.api_create_with_plan_name(
            org_uuid, space_uuid,
            ServiceLabels.SEAHORSE,
            service_plan_name=ServicePlan.FREE
        )
        self.service_instance.ensure_created()
        self.seahorse_url = "{}-{}.{}".format(self.service_instance.name, self.service_instance.guid, self.tap_domain)

        http_client_configuration = HttpClientConfiguration(
            client_type=HttpClientType.SERVICE_TOOL,
            url="https://{}".format(self.seahorse_url),
            username=self.username,
            password=self.password
        )
        self.http_client = HttpClientFactory.get(http_client_configuration)
        self.http_client.session = tap_http_client.session

        self._ensure_seahorse_accessible()
        self._ensure_wm_accessible()
        self._ensure_sm_accessible()

        self._ws = None

    def cleanup(self):
        self.service_instance.cleanup()

    @property
    def ws(self):
        if self._ws is None:
            self._ws = websocket.WebSocket()
        return self._ws

    def clone_workflow(self, workflow_id):
        response = self.http_client.request(
            HttpMethod.POST,
            path="{}/{}/clone".format(self.WORKFLOWS_PATH, workflow_id),
            body={'name': 'Cloned workflow', 'description': 'Some desc'}
        )
        cloned_workflow_id = response["workflowId"]
        self.http_client.request(
            HttpMethod.GET,
            path="{}/{}".format(self.WORKFLOWS_PATH, cloned_workflow_id)
        )
        return cloned_workflow_id

    def launch(self, workflow_id):
        msg = '["SEND\ndestination:/exchange/seahorse/workflow.' + workflow_id + '.' + workflow_id + \
              '.from\n\n{\\"messageType\\":\\"launch\\",\\"messageBody\\":{\\"workflowId\\":\\"' + \
              workflow_id + '\\",\\"nodesToExecute\\":[]}}\u0000"]'
        self.ws.send(msg)

    def assert_n_nodes_completed_successfully(self, n):
        for x in range(1, n + 1):
            logger.info('Waiting for execution status for {}. node'.format(x))
            self._ensure_node_executed_without_errors()

    def start_editing(self, workflow_id):
        self.http_client.request(HttpMethod.POST, path=self.SESSIONS_PATH, body={'workflowId': workflow_id})
        self._ensure_executor_is_running(workflow_id)

        self.ws.connect("ws://" + self.seahorse_url + "/stomp/645/bg1ozddg/websocket")
        self.ws.send("""["CONNECT\nlogin:guest\npasscode:guest\naccept-version:1.1,1.0\nheart-beat:0,0\n\n\u0000"]""")
        self.ws.send(
            """["SUBSCRIBE\nid:sub-0\ndestination:/exchange/seahorse/seahorse.{0}.to\n\n\u0000"]""".format(workflow_id))
        self.ws.send("""["SUBSCRIBE\nid:sub-1\ndestination:/exchange/seahorse/workflow.{0}.{0}.to\n\n\u0000"]""".format(
            workflow_id))

    def stop_editing(self, workflow_id):
        self.ws.close()
        self.http_client.request(HttpMethod.DELETE, path="{}/{}".format(self.SESSIONS_PATH, workflow_id))

    def get_workflow_id_by_name(self, workflow_name):
        workflows = self.get_workflows()
        return list(filter(lambda w: workflow_name in w['name'], workflows))[0]['id']

    def get_workflows(self):
        return self.http_client.request(HttpMethod.GET, path="{}".format(self.WORKFLOWS_PATH))

    @retry(Exception, tries=30, delay=30)
    def _ensure_seahorse_accessible(self):
        # Somehow test sometimes freezes on HTTPS connection - that's why there is timeout here
        with timeout(seconds=5):
            self.http_client.request(HttpMethod.GET, path="")

    @retry(Exception, tries=5, delay=10)
    def _ensure_wm_accessible(self):
        self.http_client.request(HttpMethod.GET, path=self.WORKFLOWS_PATH)

    @retry(Exception, tries=5, delay=10)
    def _ensure_sm_accessible(self):
        self.http_client.request(HttpMethod.GET, path=self.SESSIONS_PATH)

    @retry(AssertionError, tries=15, delay=5)
    def _ensure_executor_is_running(self, workflow_id):
        sessions = list(filter(lambda s: s['workflowId'] == workflow_id,
                               self.http_client.request(HttpMethod.GET, path=self.SESSIONS_PATH)["sessions"]))
        status = sessions[0]['status']
        assert status == 'running'

    @retry(Exception, tries=5, delay=5)
    def _ensure_node_executed_without_errors(self):
        msg = self._next_message_skipping_few_heartbeats()
        assert "executionStatus" in msg
        assert "FAILED" not in msg

    def _next_message_skipping_few_heartbeats(self):
        msg = self.ws.next()

        # Fixed number of heartbeats to prevent infinite loop.
        # Roughly there should be at least one non-heartbeat message per few hearbeats.
        number_of_heatbeats_to_skip = 20

        for x in range(0, number_of_heatbeats_to_skip):
            if "heartbeat" in msg or 'h' == msg or 'o' == msg:
                msg = self.ws.next()

        return msg


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)
