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
from unittest.mock import MagicMock, patch, mock_open

import pytest

from modules.tap_object_model.application import Application
from tests.fixtures.context import Context


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


def test_update_manifest():
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

def test_update_manifest_delete_services():
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

def test_update_manifest_no_envs():
    """Try not to add any envs"""
    j = copy.deepcopy(MANIFEST)

    j = Application.update_manifest(j, APP_NAME, SERVICES, None)

    assert j["type"] == APP_TYPE
    assert j["name"] == APP_NAME
    assert j["instances"] == NO_INSTANCES
    assert j["services"] == SERVICES
    assert j["env"][ENV_NAME] == ENV_VAL
    assert len(j["env"]) == 1

def test_update_manifest_with_no_envs():
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

def test_update_manifest_with_no_services():
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
def test_update_manifest_with_proxy():
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
    assert j["env"]["http_proxy"] == "http://" + HTTP_PROXY + ":911"
    assert j["env"]["https_proxy"] == "https://" + HTTP_PROXY + ":912"

mock_proxy = HTTP_PROXY
@patch("modules.tap_object_model.application.config.cf_proxy", mock_proxy)
def test_update_manifest_no_env_with_proxy():
    """Check if cf_proxy is present we get proxy env, no env is present
    in manifest"""
    j = copy.deepcopy(MANIFEST)
    del j["env"]

    j = Application.update_manifest(j, APP_NAME, SERVICES, ENVS)

    assert j["type"] == APP_TYPE
    assert j["name"] == APP_NAME
    assert j["instances"] == NO_INSTANCES
    assert j["services"] == SERVICES
    assert j["env"][NEW_ENV_01] == NEW_ENV_01_VAL
    assert j["env"][NEW_ENV_02] == NEW_ENV_02_VAL
    assert j["env"]["http_proxy"] == "http://" + HTTP_PROXY + ":911"
    assert j["env"]["https_proxy"] == "https://" + HTTP_PROXY + ":912"

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

@patch("builtins.open", mock_open)
@patch("modules.tap_object_model.application.json", mock_json)
@patch("modules.tap_object_model.application.TapCli", mock_tap_cli)
@patch("modules.tap_object_model.application.api_service", mock_api_service)
def test_push():
    """Tests standard push command"""
    ctx = Context()

    # Force the return of fake service
    mock_api_service.get_applications.return_value = GET_APP_RESPONSE

    a = Application.push(ctx, SOURCE_DIR, APP_NAME, BOUND_SERVICES,
                         ENV)
    assert a == Application(APP_NAME, APP_ID, APP_STATE, APP_INSTANCES,
                            APP_URLS)

@patch("builtins.open", mock_open)
@patch("modules.tap_object_model.application.json", mock_json)
@patch("modules.tap_object_model.application.TapCli", mock_tap_cli)
@patch("modules.tap_object_model.application.api_service", mock_api_service_bad)
def test_push_fail():
    """Try pushing the app, but it doesn't appear in the response"""
    ctx = Context()

    # Force the return of fake service
    mock_api_service_bad.api_get_app_list.return_value = GET_APP_BAD_RESPONSE

    with pytest.raises(AssertionError):
        a = Application.push(ctx, SOURCE_DIR, APP_NAME, BOUND_SERVICES,
                             ENV)

@patch("builtins.open", mock_open)
@patch("modules.tap_object_model.application.json", mock_json)
@patch("modules.tap_object_model.application.TapCli", mock_tap_cli_exception)
@patch("modules.tap_object_model.application.api_service", mock_api_service)
def test_push_tap_exception():
    """Try pushing the app, but exception was raised by TapCli"""
    ctx = Context()

    # Force the return of fake service
    mock_api_service.api_get_app_list.return_value = GET_APP_RESPONSE

    # Force the exception raising
    mock_TapCli = MagicMock()
    mock_TapCli.push.side_effect = Exception("Bang, bang!")
    mock_tap_cli_exception.return_value = mock_TapCli

    with pytest.raises(Exception):
        a = Application.push(ctx, SOURCE_DIR, APP_NAME, BOUND_SERVICES,
                             ENV)

    mock_api_service.delete_application.assert_called_once_with(app_id=APP_ID,
                                                                client=None)
