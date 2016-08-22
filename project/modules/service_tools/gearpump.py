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
from modules.tap_object_model import Application, ServiceInstance, ServiceKey
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.yarn import Yarn
from .gearpump_application import GearpumpApplication


class Gearpump(object):
    """Gearpump service instance."""

    def __init__(self, context, org_guid, space_guid, service_plan_name, instance_name=None, params=None):
        self.instance = ServiceInstance.api_create_with_plan_name(
            context=context,
            org_guid=org_guid,
            space_guid=space_guid,
            name=instance_name,
            service_label=ServiceLabels.GEARPUMP,
            service_plan_name=service_plan_name,
            params=params
        )
        self.space_guid = space_guid
        self.yarn_app_id = None
        self.client = HttpClientFactory.get(ConsoleConfigurationProvider.get())

    @retry(KeyError, tries=5, delay=5)
    def get_credentials(self):
        """Set gearpump instance credentials."""
        response = self.instance.api_get_credentials()
        self.instance.login = response["login"]
        self.instance.password = response["password"]
        self.instance.instance_url = response["hostname"]

    def go_to_dashboard(self):
        """Simulate going to gearpump dashboard"""
        self.client.url = "http://{}".format(self.instance.instance_url)
        try:
            self.client.request(
                method=HttpMethod.GET,
                path="login/oauth2/cloudfoundryuaa/authorize",
                msg="Go to dashboard"
            )
        except:
            self.go_to_console()
            raise

    def go_to_console(self):
        self.client.url = config.console_url

    def submit_application_jar(self, jar_file, application_name, extra_params=None, instance_credentials=None,
                               timeout=120) -> GearpumpApplication:
        """Submit gearpump application. Response returns only: {"success":true/false}"""
        files = {'jar': open(jar_file, 'rb')}
        request_args = {}
        if extra_params:
            request_args.update({"usersArgs": extra_params})
        if instance_credentials:
            request_args.update(instance_credentials)
        data = {"configstring": ("", "tap={}".format(json.dumps(request_args)))} if request_args else None
        response = self.client.request(
            method=HttpMethod.POST,
            path="api/v1.0/master/submitapp",
            files=files,
            data=data,
            msg="Gearpump: submit application",
            timeout=timeout
        )
        if response["success"]:
            return GearpumpApplication(application_name, self.client)

    def get_ui_app(self):
        apps = Application.api_get_list(space_guid=self.space_guid)
        gearpump_ui_app = next((app for app in apps if "gearpump-ui-{}".format(self.instance.guid) in app.name), None)
        return gearpump_ui_app

    def get_yarn_app_status(self):
        if self.yarn_app_id is None:
            gearpump_key = ServiceKey.api_create(self.instance.guid)
            self.yarn_app_id = gearpump_key.credentials["yarnApplicationId"]
            gearpump_key.api_delete()
        yarn = Yarn()
        result = yarn.get_application_details(self.yarn_app_id)
        return result["State"]
