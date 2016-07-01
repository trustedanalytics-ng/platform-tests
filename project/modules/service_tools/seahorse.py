import re
import signal

import requests
from retry import retry

from configuration import config
from modules.tap_object_model import ServiceInstance

import websocket

class Seahorse():
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]

    def __init__(self, org_uuid, space_uuid):
        service_instance = ServiceInstance.api_create_with_plan_name(
            org_uuid, space_uuid,
            self.seahorse_label,
            service_plan_name="free")

        service_instance.ensure_created()

        self.seahorse_url = service_instance.name + '-' + service_instance.guid + "." + self.tap_domain
        self.seahorse_http_url = 'https://' + self.seahorse_url
        self.sessions_url = self.seahorse_http_url + '/v1/sessions'
        self.workflows_url = self.seahorse_http_url + '/v1/workflows'

        self.session = requests.Session()
        self._ensure_seahorse_accessible()
        self._tap_log_in()

        self._ensure_wm_accessible()
        self._ensure_sm_accessible()

    def _tap_log_in(self):
        login_form = self.session.get(self.seahorse_http_url, verify=False)
        csrf_value_regex = r"x-uaa-csrf.*value=\"(.*)\""
        match = re.search(csrf_value_regex, login_form.text, re.IGNORECASE)
        csrf_value = match.group(1)
        payload = {'username': Seahorse.username, 'password': Seahorse.password, 'X-Uaa-Csrf': csrf_value}
        self.session.post(url='http://login.{0}/login.do'.format(Seahorse.tap_domain), data=payload)

    def clone_workflow(self, workflow_id):
        clone_url = self.workflows_url + '/' + workflow_id + "/clone"
        clone_resp = self.session.post(clone_url, json={'name': 'Cloned workflow', 'description': 'Some desc'})
        clone_resp.raise_for_status()
        cloned_workflow_id = clone_resp.json()['workflowId']

        self.session.get(self.workflows_url + '/' + cloned_workflow_id).raise_for_status()
        return cloned_workflow_id

    def launch(self, workflow_id):
        self.ws.send(
            '["SEND\ndestination:/exchange/seahorse/workflow.' + workflow_id + '.' + workflow_id + '.from\n\n{\\"messageType\\":\\"launch\\",\\"messageBody\\":{\\"workflowId\\":\\"' + workflow_id + '\\",\\"nodesToExecute\\":[]}}\u0000"]')

    def assert_n_nodes_completed_successfully(self, n):
        for x in range(1, n + 1):
            print('Waiting for execution status for {0}. node'.format(x))
            self._ensure_node_executed_without_errors()

    def start_editing(self, workflow_id):
        self.session.post(self.sessions_url, json={'workflowId': workflow_id})
        self._ensure_executor_is_running(workflow_id)

        self.ws = websocket.WebSocket()
        self.ws.connect("ws://" + self.seahorse_url + "/stomp/645/bg1ozddg/websocket")
        self.ws.send("""["CONNECT\nlogin:guest\npasscode:guest\naccept-version:1.1,1.0\nheart-beat:0,0\n\n\u0000"]""")
        self.ws.send(
            """["SUBSCRIBE\nid:sub-0\ndestination:/exchange/seahorse/seahorse.{0}.to\n\n\u0000"]""".format(workflow_id))
        self.ws.send("""["SUBSCRIBE\nid:sub-1\ndestination:/exchange/seahorse/workflow.{0}.{0}.to\n\n\u0000"]""".format(
            workflow_id))

    def stop_editing(self, workflow_id):
        self.ws.close()
        self.session.delete(self.sessions_url + '/' + workflow_id)

    def get_workflow_id_by_name(self, workflow_name):
        workflows = self.get_workflows()
        return list(filter(lambda w: workflow_name in w['name'], workflows))[0]['id']

    def get_workflows(self):
        return self.session.get(self.seahorse_http_url + '/v1/workflows').json()

    @retry(Exception, tries=100, delay=30)
    def _ensure_seahorse_accessible(self):
        # Somehow test sometimes freezes on HTTPS connection - thats why there is timeout here
        with timeout(seconds=5):
            self.session.get(self.seahorse_http_url, verify=False).raise_for_status()

    @retry(Exception, tries=5, delay=10)
    def _ensure_wm_accessible(self):
        response = self.session.get(self.workflows_url).raise_for_status()

    @retry(Exception, tries=5, delay=10)
    def _ensure_sm_accessible(self):
        response = self.session.get(self.sessions_url).raise_for_status()

    @retry(AssertionError, tries=15, delay=5)
    def _ensure_executor_is_running(self, workflow_id):
        sessions = list(
            filter(lambda s: s['workflowId'] == workflow_id, self.session.get(self.sessions_url).json()['sessions']))
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
