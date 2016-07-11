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

from retry import retry

from ..constants import ServiceLabels
from ..tap_object_model import ServiceInstance
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from ..http_client.http_client import HttpClient
from ..http_client.http_client_factory import HttpClientFactory
from .gearpump_application import GearpumpApplication


class Gearpump(object):
    """Gearpump service instance."""

    def __init__(self, org_guid, space_guid, service_plan_name, instance_name=None, params=None):
        self.instance = ServiceInstance.api_create_with_plan_name(
            org_guid=org_guid,
            space_guid=space_guid,
            name=instance_name,
            service_label=ServiceLabels.GEARPUMP,
            service_plan_name=service_plan_name,
            params=params
        )
        self.client = None

    def get_client(self) -> HttpClient:
        """Return gearpump http client."""
        if self.client is None:
            self.client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(
                url=self.instance.instance_url,
                username=self.instance.login,
                password=self.instance.password
            ))
        return self.client

    @retry(KeyError, tries=5, delay=5)
    def get_credentials(self):
        """Set gearpump instance credentials."""
        response = self.instance.api_get_credentials()
        self.instance.login = response["login"]
        self.instance.password = response["password"]
        self.instance.instance_url = response["hostname"]

    def login(self):
        """Login into gearpump instance."""
        data = {
            "username": self.instance.login,
            "password": self.instance.password,
        }
        self.get_client().request(
            method=HttpMethod.POST,
            path="login",
            data=data,
            msg="Gearpump: login"
        )

    def submit_application_jar(self, jar_file, application_name, timeout=None) -> GearpumpApplication:
        """Submit gearpump application. Response returns only: {"success":true/false}"""
        files = {'jar': open(jar_file, 'rb')}
        response = self.get_client().request(
            method=HttpMethod.POST,
            path="api/v1.0/master/submitapp",
            files=files,
            msg="Gearpump: submit application",
            timeout=timeout
        )
        if response["success"]:
            return GearpumpApplication(application_name, self.get_client())
