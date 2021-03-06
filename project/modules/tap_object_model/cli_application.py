#
# Copyright (c) 2017 Intel Corporation
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

from modules.constants import HttpStatus, TapEntityState
from modules.exceptions import UnexpectedResponseError
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from ._cli_object_superclass import CliObjectSuperclass
from modules.tap_cli import TapCli


class CliApplication(CliObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["name", "app_type"]
    EXPECTED_PUSH_HEADERS = ["NAME", "IMAGE ID", "DESCRIPTION", "REPLICATION"]
    EXPECTED_DELETE_BODY = 'OK'
    EXPECTED_SUCCESS_RESPONSE = 'Accepted'

    FIELD_ID = "id"
    FIELD_NAME = "NAME"
    FIELD_TYPE = "type"
    FIELD_STATE = "state"
    FIELD_URLS = "urls"

    def __init__(self, *, app_type, target_directory, tap_cli, name, instances):
        super().__init__(tap_cli=tap_cli, name=name)
        self.app_type = app_type
        self.instances = instances
        self.target_directory = target_directory
        self.type = TapCli.APPLICATION

    @classmethod
    def push(cls, context, *, app_path, tap_cli, app_type, name=None, instances=1):
        new_app = cls(app_type=app_type, target_directory=app_path,
                      tap_cli=tap_cli, name=name, instances=instances)
        context.test_objects.append(new_app)
        push_output = tap_cli.app_push(app_path=app_path)
        missing_headers = []
        for header in cls.EXPECTED_PUSH_HEADERS:
            if header not in push_output:
                missing_headers.append(header)
        assert len(missing_headers) == 0, "Headers missing in push output: {}".format(", ".join(missing_headers))
        return new_app

    def start(self):
        start_output = self.tap_cli.app_start(application_name=self.name)
        assert self.EXPECTED_SUCCESS_RESPONSE in start_output
        return start_output

    def stop(self):
        stop_output = self.tap_cli.app_stop(application_name=self.name)
        assert self.EXPECTED_SUCCESS_RESPONSE in stop_output
        return stop_output

    def restart(self):
        """Attempts to restart application

        Returns:
            Command output

        Raises:
            CommandExecutionException
        """
        output = self.tap_cli.app_restart(application_name=self.name)
        assert self.EXPECTED_SUCCESS_RESPONSE in output
        return output

    def scale(self, scale_app_instances):
        scale_output = self.tap_cli.app_scale(application_name=self.name, instances=scale_app_instances)
        assert self.EXPECTED_SUCCESS_RESPONSE in scale_output
        return scale_output

    def bind(self, bound_app, direction):
        out = self.tap_cli.bind(self.type, [TapCli.NAME_PARAM, self.name, direction, bound_app])
        assert self.EXPECTED_SUCCESS_RESPONSE

    def unbind(self, bound_app, direction):
        out = self.tap_cli.unbind(self.type, [TapCli.NAME_PARAM, self.name, direction, bound_app])

    def logs(self):
        return self.tap_cli.app_logs(application_name=self.name)

    def delete(self):
        if self._is_deleted is True:
            return

        try:
            delete = self.tap_cli.app_delete(application_name=self.name)
            assert self.EXPECTED_DELETE_BODY in delete
            self.ensure_not_on_app_list()
            self._set_deleted(True)
        except UnexpectedResponseError:
            raise

        return delete

    def get_details(self):
        return self.tap_cli.app_info(application_name=self.name)

    def get_running_instances(self):
        return self.get_details()["running_instances"]

    def ensure_info_about_app_was_correct(self, name, image_type):
        app = self.get_details()
        assert app["name"] == name
        assert app["imageType"] == image_type

    @retry(AssertionError, tries=12, delay=5)
    def ensure_on_app_list(self):
        app = next((app for app in self.tap_cli.app_list() if app[self.FIELD_NAME] == self.name), None)
        assert app is not None, "App '{}' is not on the list of apps".format(self.name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_not_on_app_list(self):
        app = next((app for app in self.tap_cli.app_list() if app[self.FIELD_NAME] == self.name), None)
        assert app is None, "App '{}' is on the list of apps".format(self.name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_state(self, state):
        app = self.get_details()
        assert app is not None, "Application {} was not found".format(self.name)
        msg = "Expected state '{}' but was '{}'".format(state, app[self.FIELD_STATE])
        # Stop rerunning when the app is in FAILURE state.
        if app[self.FIELD_STATE] == TapEntityState.FAILURE and state != app[self.FIELD_STATE]:
            raise ValueError(msg)
        assert app[self.FIELD_STATE] == state, msg

    @retry(AssertionError, tries=12, delay=5)
    def ensure_app_is_ready(self):
        url = self.get_details()[self.FIELD_URLS][0]
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
        app = self.tap_cli.app_info(self.name)
        assert app is not None, "Application {} was not found".format(self.name)
        assert isinstance(app, dict)
        assert app[self.FIELD_ID] is not None
        return app[self.FIELD_ID]

    def cleanup(self):
        if self.get_details()[self.FIELD_STATE] == TapEntityState.RUNNING:
            self.stop()
            self.ensure_app_state(TapEntityState.STOPPED)
        self.delete()
