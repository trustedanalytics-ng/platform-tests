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
#from modules.tap_object_model.application import Application
import json
import copy

import pytest
from unittest.mock import patch
from unittest.mock import MagicMock

from modules.tap_object_model.application import Application

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
