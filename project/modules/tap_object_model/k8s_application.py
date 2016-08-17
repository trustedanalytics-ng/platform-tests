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

import functools

from retry import retry

from modules.constants import HttpStatus
from modules.constants.urls import Urls
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.tap_object_model.console_service import ConsoleService
from tests.fixtures.assertions import assert_raises_http_exception, assert_returns_http_success_with_retry


@functools.total_ordering
class K8sApplication(object):
    STATE_RUNNING = "RUNNING"
    STATE_STOPPED = "STOPPED"

    url = None

    def __init__(self, app_id: str, name: str, app_type: str, class_id: str, bindings, metadata,  state: str,
                 created_on, created_by, last_updated_on, last_update_by, replication, image_state):
        self.id = app_id
        self.name = name
        self.type = app_type
        self.class_id = class_id
        self.bindings = bindings
        self.metadata = metadata
        self.state = state
        self.created_on = created_on
        self.created_by = created_by
        self.last_updated_on = last_updated_on
        self.last_update_by = last_update_by
        self.replication = replication
        self.image_state = image_state

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def push(cls, context, file_path, manifest_path):
        assert file_path is not None, "File path is not set"
        assert manifest_path is not None, "Manifest path is not set"
        response = ConsoleService.push_application(file_path, manifest_path)
        new_app = cls._from_response(response)
        context.k8s_apps.append(new_app)
        return new_app

    @classmethod
    def get(cls, app_id: str):
        response = ConsoleService.get_application(app_id)
        app = cls._from_response(response)
        return app

    @retry(AssertionError, tries=6, delay=5)
    def ensure_running(self):
        app = self.get(self.id)
        assert app.state == self.STATE_RUNNING

    @retry(AssertionError, tries=6, delay=5)
    def ensure_stopped(self):
        app = self.get(self.id)
        assert app.state == self.STATE_STOPPED

    def get_http_client(self, url):
        client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=url))
        return client

    def send_request(self, path=""):
        assert self.url is not None, "Application url is not set"
        client = self.get_http_client(self.url)
        response = client.request(
            method=HttpMethod.GET,
            path=path,
            raw_response=True,
            raise_exception=True,
            msg="K8sApplication: get /{}".format(path)
        )
        return response

    @retry(AssertionError, tries=6, delay=5)
    def ensure_ready(self):
        assert_returns_http_success_with_retry(self.send_request)

    @retry(AssertionError, tries=6, delay=5)
    def ensure_is_down(self):
        assert_raises_http_exception(HttpStatus.CODE_GATEWAY_TIMEOUT, "",
                                     self.send_request)

    def check_healthz(self):
        response = self.send_request("healthz")
        return response

    def delete(self):
        ConsoleService.delete_application(self.id)

    def cleanup(self):
        self.delete()

    def scale(self, replicas):
        response = ConsoleService.scale_application(self.id, replicas)
        return response

    def stop(self):
        response = ConsoleService.stop_application(self.id)
        return response

    def start(self):
        response = ConsoleService.start_application(self.id)
        return response

    def get_logs(self):
        response = ConsoleService.get_application_logs(self.id)
        return response

    @classmethod
    def _from_response(cls, response):
        response = response.json()
        return cls(app_id=response["id"], name=response["name"], app_type=response["type"],
                   class_id=response["classId"], bindings=response["bindings"], metadata=response["metadata"],
                   state=response["state"], created_on=response["auditTrail"]["createdOn"],
                   created_by=response["auditTrail"]["createdBy"],
                   last_updated_on=response["auditTrail"]["lastUpdatedOn"],
                   last_update_by=response["auditTrail"]["lastUpdateBy"], replication=response["replication"],
                   image_state=response["imageState"])
