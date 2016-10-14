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

import pytest

import config
import tests.fixtures.assertions as assertions
from modules.constants import TapComponent as TAP
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import Application, Organization, ServiceInstance, User


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_create_and_delete_organization(context):
    """Create and Delete Organization"""
    step("Create organization")
    test_org = Organization.create(context)
    step("Check that organization is on the list")
    orgs = Organization.get_list()
    assert test_org in orgs
    step("Delete organization")
    test_org.delete()
    step("Check that the organization is not on the list")
    assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - ATK")
@pytest.mark.components(TAP.atk)
def test_connect_to_atk_from_jupyter_using_default_atk_client(context, request, core_space, test_space, test_org,
                                                              admin_user):
    """Connect to Atk from Jupyter using Default Atk Client"""
    step("Get atk app from core space")
    atk_app = next((app for app in Application.get_list() if app.name == "atk"), None)
    if atk_app is None:
        raise AssertionError("Atk app not found in core space")
    atk_url = atk_app.urls[0]
    step("Add admin to test space")
    admin_user.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid, roles=User.SPACE_ROLES["developer"])
    step("Create instance of Jupyter service")
    jupyter = Jupyter(context=context, org_guid=test_org.guid, space_guid=test_space.guid)
    assertions.assert_in_with_retry(jupyter.instance, ServiceInstance.api_get_list, space_guid=test_space.guid)
    step("Get credentials for the new jupyter service instance")
    jupyter.get_credentials()
    step("Login into Jupyter")
    jupyter.login()
    request.addfinalizer(lambda: jupyter.instance.api_delete())
    step("Create new Jupyter notebook")
    notebook = jupyter.create_notebook()
    step("import atk client in the notebook")
    notebook.send_input("import trustedanalytics as ta")
    assert notebook.check_command_status() == "ok"
    step("Create credentials file using atk client")
    notebook.send_input("ta.create_credentials_file('./cred_file')")
    assert "URI of the ATK server" in notebook.get_prompt_text()
    notebook.send_input(atk_url, reply=True)
    assert "User name" in notebook.get_prompt_text()
    notebook.send_input(config.admin_username, reply=True)
    assert "" in notebook.get_prompt_text()
    notebook.send_input(config.admin_password, reply=True, obscure_from_log=True)
    assert "Connect now?" in notebook.get_prompt_text()
    notebook.send_input("y", reply=True)
    assert "Connected." in str(notebook.get_stream_result())
    notebook.ws.close()
