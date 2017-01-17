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

from retry import retry

import config
from modules.constants import ServiceLabels
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.ssh_lib.jump_client import JumpClient
from modules.tap_object_model import ServiceInstance
from .gearpump_application import GearpumpApplication


class Gearpump(object):
    """Gearpump service instance."""

    def __init__(self, context, service_plan_name, instance_name=None, params=None):
        self.instance = ServiceInstance.create_with_name(
            context=context,
            offering_label=ServiceLabels.GEARPUMP,
            name=instance_name,
            plan_name=service_plan_name,
            params=params
        )
        self.yarn_app_id = None
        self.client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
        self.ssh_client = None
        self._gearpump_url = None

    @retry(KeyError, tries=5, delay=5)
    def get_credentials(self):
        """Set gearpump instance credentials."""
        response = self.instance.get_credentials(self.instance.id, self.client)
        credentials = response[0].get("envs")
        self.instance.login = credentials["username"]
        self.instance.password = credentials["password"]
        self.instance.instance_url = credentials["dashboardUrl"]

    def go_to_dashboard(self):
        """Simulate going to gearpump dashboard"""
        self._gearpump_url = "http://{}".format(self.instance.instance_url)

        try:
            self.client.request(
                method=HttpMethod.GET,
                url=self._gearpump_url,
                path="login/oauth2/cloudfoundryuaa/authorize",
                msg="Go to dashboard"
            )
        except:
            raise

    def get_gearpump_application(self, jar_file, application_name, extra_params=None, instance_credentials=None,
                                 timeout=120) -> GearpumpApplication:
        files = {'jar': open(jar_file, 'rb')}
        request_args = {}
        if extra_params:
            request_args.update({"usersArgs": extra_params})
        if instance_credentials:
            request_args.update(instance_credentials)
        data = {"configstring": ("", "tap={}".format(json.dumps(request_args)))} if request_args else None
        response = self.client.request(
            method=HttpMethod.POST,
            url=self._gearpump_url,
            path="api/v1.0/master/submitapp",
            files=files,
            data=data,
            msg="Gearpump: submit application",
            timeout=timeout
        )
        if response["success"]:
            return GearpumpApplication(application_name, self.client, self._gearpump_url)

    def get_ui_app(self):
        apps = self.instance.get_list(name="gp-ui-{}".format(self.instance.id))
        gearpump_ui_app = apps[0] if apps else None
        return gearpump_ui_app

    def get_yarn_app_status(self):
        """
        Get yarn_app status.
        """
        if self.ssh_client is None:
            self.set_ssh_client()
        self.yarn_endpoint = "https://{}.instance.cluster.local:8090/ws/v1/cluster/apps/"
        if self.yarn_app_id is None:
            self.get_yarn_id()
        if config.kerberos:
            self.yarn_endpoint = self.yarn_endpoint.format("hadoop-master-0")
        else:
            self.yarn_endpoint = self.yarn_endpoint.format("hadoop-master-1")
        url = self.yarn_endpoint + self.yarn_app_id
        command = ["curl --insecure", url]
        response = self.ssh_client.execute_ssh_command(command)
        string = next(i for i in response if 'state' in i)
        start_json = string.find('{')
        json_string = string[start_json:]
        json_obj = json.loads(json_string)
        return str(json_obj["app"]["state"])

    def get_yarn_id(self):
        """
        Get yarn_id from service instance.
        """
        response = self.instance.get_credentials(self.instance.id, self.client)
        credentials = response[0].get("envs")
        self.yarn_app_id = credentials["yarnApplicationId"]

    def set_ssh_client(self):
        self.ssh_client = JumpClient(remote_host=config.jumpbox_hostname, remote_username=config.ng_jump_user,
                                     remote_key_path=config.jumpbox_key_path)
