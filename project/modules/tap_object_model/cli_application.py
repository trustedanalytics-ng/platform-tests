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

import os
import shutil

from retry import retry

from modules.constants import HttpStatus
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from modules.tap_object_model import Application
from modules.test_names import generate_test_object_name
from ._cli_object_superclass import CliObjectSuperclass


class CliApplication(CliObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["name", "app_type"]
    EXPECTED_PUSH_HEADERS = ["NAME", "IMAGE ID", "DESCRIPTION", "REPLICATION"]
    EXPECTED_DELETE_BODY = 'CODE: 204 BODY'
    EXPECTED_SUCCESS_RESPONSE = 'success'

    def __init__(self, *, app_type, target_directory, tap_cli, name, instances):
        super().__init__(tap_cli=tap_cli, name=name)
        self.app_type = app_type
        self.instances = instances
        self.target_directory = target_directory

    @classmethod
    def _update_manifest(cls, *, manifest_path, target_directory, app_type, name, instances):
        manifest_params = {
            'instances': instances,
            'name': name,
            'type': app_type
        }
        Application.update_manifest(manifest_path, manifest_params)
        shutil.copyfile(manifest_path, os.path.join(target_directory, "manifest.json"))

    @classmethod
    def push(cls, context, *, app_path, tap_cli, app_type, name=None, instances=1, bindings: list=None):
        if name is None:
            name = generate_test_object_name(separator="-")
        Application.save_manifest(app_path=app_path, name=name, instances=instances, app_type=app_type, bindings=bindings)
        new_app = cls(app_type=app_type, target_directory=app_path, tap_cli=tap_cli, name=name, instances=instances)
        context.test_objects.append(new_app)
        push_output = tap_cli.push(app_path=app_path)
        missing_headers = []
        for header in cls.EXPECTED_PUSH_HEADERS:
            if header not in push_output:
                missing_headers.append(header)
        assert len(missing_headers) == 0, "Headers missing in push output: {}".format(", ".join(missing_headers))
        return new_app

    def start(self):
        start_output = self.tap_cli.start_app(application_name=self.name)
        assert self.EXPECTED_SUCCESS_RESPONSE in start_output
        return start_output

    def stop(self):
        stop_output = self.tap_cli.stop_app(application_name=self.name)
        assert self.EXPECTED_SUCCESS_RESPONSE in stop_output
        return stop_output

    def scale(self, scale_app_instances):
        scale_output = self.tap_cli.scale_app(application_name=self.name, instances=scale_app_instances)
        assert self.EXPECTED_SUCCESS_RESPONSE in scale_output
        return scale_output

    def logs(self):
        return self.tap_cli.app_logs(application_name=self.name)

    def delete(self):
        delete = self.tap_cli.delete_app(application_name=self.name)
        assert self.EXPECTED_DELETE_BODY in delete
        self.ensure_not_on_app_list()
        return delete

    def get_details(self):
        return self.tap_cli.app(application_name=self.name)

    def get_running_instances(self):
        return self.get_details()["running_instances"]

    @retry(AssertionError, tries=12, delay=5)
    def ensure_on_app_list(self):
        self.tap_cli.ensure_app_availability_on_the_list(self.name, should_be_on_the_list=True)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_not_on_app_list(self):
        self.tap_cli.ensure_app_availability_on_the_list(self.name, should_be_on_the_list=False)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_state(self, state):
        app = self.tap_cli.app(application_name=self.name)
        assert app is not None, "Application {} was not found".format(self.name)
        assert app["state"] == state, "Expected state '{}' but was '{}'".format(state, app['state'])

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_is_ready(self):
        url = self.get_details()["urls"][0]
        client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=url))
        response = client.request(
            method=HttpMethod.GET,
            path="",
            raw_response=True,
            raise_exception=True,
            msg="Send GET to application {}".format(self.name)
        )
        assert response.status_code == HttpStatus.CODE_OK

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_has_id(self):
        app = self.tap_cli.app(self.name)
        assert app.get("id", None) is not None
        return app["id"]
