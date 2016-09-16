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
"""Unit tests for Application class"""
import copy
import unittest
from unittest.mock import MagicMock, patch, mock_open

import pytest

import sys
sys.path.append("/home/local/GER/kmolon/repos/platform-tests/project")

from modules.tap_object_model.application import Application
from tests.fixtures.context import Context
from modules.exceptions import UnexpectedResponseError


APP_TYPE = 'JAVA'
OLD_APP_NAME = 'app'
NO_INSTANCES = 2
SERVICE_NAME = 'basic_service'
ENV_NAME = "env_name"
ENV_VAL = "env_value"
MANIFEST = {
    "type" : APP_TYPE,
    "name" : OLD_APP_NAME,
    "instances" : NO_INSTANCES,
    "services" : [SERVICE_NAME],
    "env" : {
        ENV_NAME : ENV_VAL
    }
}

APP_NAME = "new-app-name"
SERVICES = ['service_01', 'service_02']
NEW_ENV_01 = "envy"
NEW_ENV_01_VAL = "asdf"
NEW_ENV_02 = "variable"
NEW_ENV_02_VAL = "1234"
ENVS = [(NEW_ENV_01, NEW_ENV_01_VAL), (NEW_ENV_02, NEW_ENV_02_VAL)]

class TestApplication(unittest.TestCase):
    def test_update_manifest(self):
        """Tests if update manifest method works."""
        j = copy.deepcopy(MANIFEST)

        j = Application.update_manifest(j, APP_NAME, SERVICES, ENVS)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"][ENV_NAME] == ENV_VAL
        assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
        assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL

    def test_update_manifest_delete_services(self):
        """Deletes services provided already present in manifest"""
        j = copy.deepcopy(MANIFEST)

        j = Application.update_manifest(j, APP_NAME, None, ENVS)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        with pytest.raises(KeyError):
            j["services"]
        assert j["env"][ENV_NAME] == ENV_VAL
        assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
        assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL

    def test_update_manifest_no_envs(self):
        """Try not to add any envs"""
        j = copy.deepcopy(MANIFEST)

        j = Application.update_manifest(j, APP_NAME, SERVICES, None)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"][ENV_NAME] == ENV_VAL
        assert len(j["env"]) == 1

    def test_update_manifest_with_no_envs(self):
        """Update a manifest that has no envs defined"""
        j = copy.deepcopy(MANIFEST)
        del j["env"]

        j = Application.update_manifest(j, APP_NAME, SERVICES, ENVS)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
        assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL
        assert len(j["env"]) == 2

    def test_update_manifest_with_no_services(self):
        """Update a manifest that has no services defines"""
        j = copy.deepcopy(MANIFEST)
        del j["services"]

        j = Application.update_manifest(j, APP_NAME, SERVICES, ENVS)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"][ENV_NAME] == ENV_VAL
        assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
        assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL

    HTTP_PROXY = "951.27.9.840"

    mock_proxy = HTTP_PROXY
    @patch("modules.tap_object_model.application.config.cf_proxy", mock_proxy)
    def test_update_manifest_with_proxy(self):
        """Check if cf_proxy is present we get proxy env"""
        j = copy.deepcopy(MANIFEST)

        j = Application.update_manifest(j, APP_NAME, SERVICES, ENVS)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"][ENV_NAME] == ENV_VAL
        assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
        assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL
        assert j["env"]["http_proxy"] == "http://" + self.HTTP_PROXY + ":911"
        assert j["env"]["https_proxy"] == "https://" + self.HTTP_PROXY + ":912"

    mock_proxy = HTTP_PROXY
    @patch("modules.tap_object_model.application.config.cf_proxy", mock_proxy)
    def test_update_manifest_no_env_with_proxy(self):
        """Check if cf_proxy is present we get proxy env, no env is present
        in manifest, envs provided by user"""
        j = copy.deepcopy(MANIFEST)
        del j["env"]

        j = Application.update_manifest(j, APP_NAME, SERVICES, ENVS)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
        assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL
        assert j["env"]["http_proxy"] == "http://" + self.HTTP_PROXY + ":911"
        assert j["env"]["https_proxy"] == "https://" + self.HTTP_PROXY + ":912"
        assert len(j["env"]) == 4

    mock_proxy = HTTP_PROXY
    @patch("modules.tap_object_model.application.config.cf_proxy", mock_proxy)
    def test_update_manifest_no_env_with_proxy_no_env(self):
        """Check if cf_proxy is present we get proxy env, no env is present
        in manifest, no envs were provided"""
        j = copy.deepcopy(MANIFEST)
        del j["env"]

        j = Application.update_manifest(j, APP_NAME, SERVICES, None)

        assert j["type"] == APP_TYPE
        assert j["name"] == APP_NAME
        assert j["instances"] == NO_INSTANCES
        assert j["services"] == SERVICES
        assert j["env"]["http_proxy"] == "http://" + self.HTTP_PROXY + ":911"
        assert j["env"]["https_proxy"] == "https://" + self.HTTP_PROXY + ":912"
        assert len(j["env"]) == 2

    SOURCE_DIR = "/tmp/intel/app/dir"
    APP_NAME = "el_generico"
    APP_ID = "f59649a1-5f29-4de3-6dcd-5a34ac58def4"
    APP_STATE = "RUNNING"
    APP_INSTANCES = 1
    APP_URLS = [
        "http://thelonganduselesswebaddressthatnoonewillremember.com",
        "http://ashortandfriendlywebaddressthatseasytorememeber.com"
    ]
    BOUND_SERVICES = ["service_01", "service_02"]
    ENV = {"env_01" : "env_01_val", "env_02" : "env_02_val"}

    class DummyResponse():
        def __init__(self, data):
            self.data = data

        def json(self):
            return self.data

    GET_APP_RESPONSE = DummyResponse([{
        "id": APP_ID,
        "name": APP_NAME,
        "type": "",
        "classId": "",
        "bindings": "",
        "metadata": [{
            "key": "APPLICATION_IMAGE_ID",
            "value": "127.0.0.1:30000/3486ecac-1bd8-45f7-6ec1-1307f1bcf208"
        }],
        "state": APP_STATE,
        "auditTrail": {
            "createdOn": 1473330276,
            "createdBy": "admin",
            "lastUpdatedOn": 1473330276,
            "lastUpdateBy": "admin"
        },
        "replication": 1,
        "imageState": "READY",
        "urls": APP_URLS,
        "imageType": "PYTHON",
        "memory": "256MB",
        "disk_quota": "1024MB",
        "running_instances": APP_INSTANCES
    }])

    GET_APP_BAD_RESPONSE = DummyResponse([{
        "id": APP_ID,
        "name": "non-existing-name",
        "type": "",
        "classId": "",
        "bindings": "",
        "metadata": [{
            "key": "APPLICATION_IMAGE_ID",
            "value": "127.0.0.1:30000/3486ecac-1bd8-45f7-6ec1-1307f1bcf208"
        }],
        "state": APP_STATE,
        "auditTrail": {
            "createdOn": 1473330276,
            "createdBy": "admin",
            "lastUpdatedOn": 1473330276,
            "lastUpdateBy": "admin"
        },
        "replication": 1,
        "imageState": "READY",
        "urls": APP_URLS,
        "imageType": "PYTHON",
        "memory": "256MB",
        "disk_quota": "1024MB",
        "running_instances": APP_INSTANCES
    }])

    mock_open = mock_open()
    mock_json = MagicMock()
    mock_tap_cli = MagicMock()
    mock_tap_cli_exception = MagicMock()
    mock_api_service = MagicMock()
    mock_api_service_bad = MagicMock()
    mock_api_conf = MagicMock()
    mock_http_client_factory = MagicMock()

    user_admin = {"user": "admin"}
    user_luser = {"user": "luser"}

    mock_http_client_factory.get.return_value = user_admin

    @patch("builtins.open", mock_open)
    @patch("modules.tap_object_model.application.json", mock_json)
    @patch("modules.tap_object_model.application.TapCli", mock_tap_cli)
    @patch("modules.tap_object_model.application.api_service", mock_api_service)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_push(self):
        """Tests standard push command"""
        ctx = Context()

        # Force the return of fake service
        self.mock_api_service.get_applications.return_value = self.GET_APP_RESPONSE

        a = Application.push(ctx, source_directory=self.SOURCE_DIR,
                             name=self.APP_NAME,
                             bound_services=self.BOUND_SERVICES, env=self.ENV)

        assert a == Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                                self.APP_INSTANCES, self.APP_URLS)

        assert a._client == self.user_admin

        # Now push the application but with non-standard client
        a = Application.push(ctx, source_directory=self.SOURCE_DIR,
                             name=self.APP_NAME,
                             bound_services=self.BOUND_SERVICES, env=self.ENV,
                             client=self.user_luser)

        assert a == Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                                self.APP_INSTANCES, self.APP_URLS)

        assert a._client == self.user_luser

    @patch("builtins.open", mock_open)
    @patch("modules.tap_object_model.application.json", mock_json)
    @patch("modules.tap_object_model.application.TapCli", mock_tap_cli)
    @patch("modules.tap_object_model.application.api_service", mock_api_service_bad)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_push_fail(self):
        """Try pushing the app, but it doesn't appear in the response"""
        ctx = Context()

        # Force the return of fake service
        self.mock_api_service_bad.api_get_app_list.return_value = self.GET_APP_BAD_RESPONSE

        with pytest.raises(AssertionError):
            a = Application.push(ctx, self.SOURCE_DIR, self.APP_NAME,
                                 self.BOUND_SERVICES, self.ENV)

    @patch("builtins.open", mock_open)
    @patch("modules.tap_object_model.application.json", mock_json)
    @patch("modules.tap_object_model.application.TapCli", mock_tap_cli_exception)
    @patch("modules.tap_object_model.application.api_service", mock_api_service)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_push_tap_exception(self):
        """Try pushing the app, but exception was raised by TapCli"""
        ctx = Context()

        # Force the return of fake service
        self.mock_api_service.api_get_app_list.return_value = self.GET_APP_RESPONSE

        # Force the exception raising
        mock_TapCli = MagicMock()
        mock_TapCli.push.side_effect = Exception("Bang, bang!")
        self.mock_tap_cli_exception.return_value = mock_TapCli

        with pytest.raises(Exception):
            a = Application.push(ctx, self.SOURCE_DIR, self.APP_NAME,
                                 self.BOUND_SERVICES, self.ENV)

        self.mock_api_service.delete_application.assert_called_once_with(self.user_admin,
                                                                         self.APP_ID)


    @patch("builtins.open", mock_open)
    @patch("modules.tap_object_model.application.json", mock_json)
    @patch("modules.tap_object_model.application.TapCli", mock_tap_cli)
    @patch("modules.tap_object_model.application.api_service", mock_api_service_bad)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_push_not_created(self):
        """Try pushing the app, the push succedeed, but somehow the application
        isn't visible. Ensure the message is informative."""
        ctx = Context()

        # Force the return of fake service
        self.mock_api_service_bad.api_get_app_list.return_value = []

        with pytest.raises(AssertionError) as ex:
            a = Application.push(ctx, self.SOURCE_DIR, self.APP_NAME,
                                 self.BOUND_SERVICES, self.ENV)

        msg = "App " + self.APP_NAME + " has not been created on the Platform"
        assert msg in ex.__str__()

    @patch("builtins.open", mock_open)
    @patch("modules.tap_object_model.application.json", mock_json)
    @patch("modules.tap_object_model.application.TapCli", mock_tap_cli)
    @patch("modules.tap_object_model.application.api_service", mock_api_service)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_push_has_stopped(self):
        """Pushes an application that will be in stopped state. Verifies that
        the is_stopped property doesn't crash anything."""
        ctx = Context()

        # Force the return of fake service
        rep = copy.deepcopy(self.GET_APP_RESPONSE)
        rep.data[0]["state"] = "stopped"
        self.mock_api_service.get_applications.return_value = rep

        a = Application.push(ctx, source_directory=self.SOURCE_DIR,
                             name=self.APP_NAME,
                             bound_services=self.BOUND_SERVICES, env=self.ENV)

        assert a == Application(self.APP_NAME, self.APP_ID, "stopped",
                                self.APP_INSTANCES, self.APP_URLS)
        assert a._client == self.user_admin
        assert a.is_stopped == True
        assert a.is_running == False

    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_lt_comparator(self):
        """Ensure the lt comparator doesn't crash anything."""
        a = Application(self.APP_NAME, "00100", self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        b = Application(self.APP_NAME, "01000", self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        assert a < b

    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_repr(self):
        """Ensure the __repr__ doesn't crash anything."""
        a = Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        assert a.__repr__() == "Application (name=" + self.APP_NAME + ", app_id=" + self.APP_ID + ")"

    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_hash(self):
        """Ensure the __hash__ doesn't crash anything."""
        a = Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        assert a.__hash__() == hash((a.name, a.app_id))

    @patch("modules.tap_object_model.application.api_service", mock_api_service)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_start_stop(self):
        """Check if proper apis are called for start and stop operations"""
        a = Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        a.api_start()
        self.mock_api_service.start_application.assert_called_once_with(self.user_admin,
                                                                        self.APP_ID)

        a.api_stop()
        self.mock_api_service.stop_application.assert_called_once_with(self.user_admin,
                                                                       self.APP_ID)

        # Provide a non-standard client
        a = Application(self.APP_NAME, self.APP_ID, self.APP_STATE, [], [],
                        None, self.user_luser)

        a.api_start()
        self.mock_api_service.start_application.assert_called_with(self.user_luser,
                                                                   self.APP_ID)

        a.api_stop()
        self.mock_api_service.stop_application.assert_called_with(self.user_luser,
                                                                  self.APP_ID)

    @patch("modules.tap_object_model.application.api_service", mock_api_service)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_app_get(self):
        """Check that get returns proper details"""

        example_response = {
            "command": "sudo rm -rf /",
            "detected_buildpack": "propably outdated",
            "disk_quota": "insufficient",
            "routes": [{
                "host": "not the one accessible",
                "domain": {
                    "name" : "The one that you won't afford"
                }
            },
            {
                "host": "also not the one accessible",
                "domain": {
                    "name" : "Also the one that you won't afford"
                }
            }],
            "environment_json" : "ls = rm -rf",
            "instances": None,
            "memory": "Good, but only short-term",
            "package_updated_at": "That's personal",
            "running_instances": "There are no instances, go figure...",
            "services": [{
                "name" : "service_01"
            },
            {
                "name" : "service_00"
            }]
        }

        expected_response = copy.deepcopy(example_response)
        del expected_response["routes"]
        del expected_response["services"]

        expected_response["domains"] = ["also not the one accessible.Also the one that you won't afford",
                                        "not the one accessible.The one that you won't afford"]
        expected_response["service_names"] = ["service_00", "service_01"]
        self.mock_api_service.get_application.return_value = example_response

        a = Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        assert expected_response == a.get()

    mock_requests = MagicMock()
    mock_log_http_request = MagicMock()
    mock_log_http_response = MagicMock()
    @patch("modules.tap_object_model.application.requests", mock_requests)
    @patch("modules.tap_object_model.application.log_http_request", mock_log_http_request)
    @patch("modules.tap_object_model.application.log_http_response", mock_log_http_response)
    @patch("modules.tap_object_model.application.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.application.HttpClientFactory", mock_http_client_factory)
    def test_request_session(self):
        """Check if proper apis are called for start and stop operations"""
        raw_req = {}
        req = {"request": ""}
        # Return itself, no need to create a new mock in this case
        self.mock_requests.session.return_value = self.mock_requests
        self.mock_requests.prepare_request.return_value = req
        self.mock_requests.Request.return_value = raw_req

        rsp = {"response": ""}
        self.mock_requests.send.return_value = rsp
        a = Application(self.APP_NAME, self.APP_ID, self.APP_STATE,
                        self.APP_INSTANCES, self.APP_URLS)

        path = "predefined"
        method = "GET"
        scheme = "http"
        hostname = "host"
        data = {"some_data" : "123"}
        params = {"params" : "321"}
        body = {"body": "body"}
        raw = True

        expected_url = scheme + "://" + hostname + "/" + path

        assert rsp == a.api_request(path, method, scheme, hostname, data,
                                    params, body, raw)
        self.mock_requests.prepare_request.assert_called_with(raw_req)
        self.mock_requests.Request.assert_called_with(method=method,
                                                      url=expected_url, params=params,
                                                      data=data, json=body)
        self.mock_requests.send.assert_called_with(req)

        # Now the response won't be OK, assertion error should raise
        class Object():
            pass
        rsp = Object()
        rsp.ok = False
        rsp.status_code = 404
        rsp.text = "Not found"
        self.mock_requests.send.return_value = rsp

        with pytest.raises(UnexpectedResponseError):
            a.api_request(path, method, scheme, hostname, data,
                          params, body, False)

if __name__ == "__main__":
    unittest.main()

