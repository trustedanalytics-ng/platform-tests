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
import re

import pytest
import requests

from modules import app_sources
from configuration import config
from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import TapComponent as TAP, ServiceCatalogHttpStatus, ServiceLabels, ServicePlan, TapGitHub, \
    RelativeRepositoryPaths as RepoPath
from modules.markers import components, incremental, long, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceKey, Application, DataSet
from modules.tap_object_model.flows import data_catalog
from tests.fixtures import assertions
from modules.service_tools.atk import ATKtools


logged_components = (TAP.scoring_engine, TAP.service_catalog, TAP.application_broker, TAP.das, TAP.hdfs_downloader,
                     TAP.metadata_parser)
pytestmark = [components.scoring_engine, components.service_catalog, components.application_broker]


@pytest.fixture(scope="class")
def space_shuttle_sources():
    step("Get space shuttle example app sources")
    example_app_sources = app_sources.AppSources.from_github(
        repo_name=TapGitHub.space_shuttle_demo,
        repo_owner=TapGitHub.intel_data,
        gh_auth=config.CONFIG["github_auth"],
    )
    return example_app_sources.path


@pytest.fixture(scope="class")
def space_shuttle_model_input(request, test_org, test_space, add_admin_to_test_org, class_context,
                              space_shuttle_sources):
    model_path = os.path.join(space_shuttle_sources, RepoPath.space_shuttle_model_input_data)
    step("Submit model as a transfer")
    _, data_set = data_catalog.create_dataset_from_file(class_context, org=test_org, file_path=model_path)
    return data_set.target_uri


@pytest.fixture(scope="class")
def atk_virtualenv(request):
    virtualenv = ATKtools("space_shuttle_virtualenv")
    virtualenv.create()

    def fin():
        try:
            virtualenv.teardown()
        except:
            pass
    request.addfinalizer(fin)
    return virtualenv


@pytest.fixture(scope="class")
def core_atk_app(core_space):
    app_list = Application.api_get_list(core_space.guid)
    atk_app = next((app for app in app_list if app.name == ServiceLabels.ATK), None)
    assert atk_app is not None, "Atk not found in core space"
    return atk_app


@long
@priority.high
@incremental
class TestScoringEngineInstance:
    expected_se_bindings = [ServiceLabels.KERBEROS, ServiceLabels.HDFS]
    ATK_MODEL_NAME = "model_name"  # name is hardcoded in atk_model_generator.py - task for changing the name DPNG-8390

    def test_0_get_atk_model(self, atk_virtualenv, core_atk_app, core_org, space_shuttle_sources,
                             space_shuttle_model_input):
        step("Check if there already is an atk model generated")
        data_sets = DataSet.api_get_list(org_list=[core_org])
        atk_model_dataset = next((ds for ds in data_sets if ds.title == self.ATK_MODEL_NAME), None)
        if atk_model_dataset is not None:
            self.__class__.atk_model_uri = atk_model_dataset.target_uri
        else:
            step("Install atk client package")
            atk_url = core_atk_app.urls[0]
            atk_virtualenv.pip_install(ATKtools.get_atk_client_url(atk_url))
            step("Generate new atk model")
            atk_model_generator_path = os.path.join(space_shuttle_sources, RepoPath.space_shuttle_model_generator)
            atk_generator_output = atk_virtualenv.run_atk_script(atk_model_generator_path, atk_url,
                                                                 positional_arguments=[space_shuttle_model_input],
                                                                 use_uaa=False)
            pattern = r"(hdfs://[a-zA-Z0-9/\-_]*\.tar)"
            self.__class__.atk_model_uri = re.search(pattern, atk_generator_output).group()
        assert self.atk_model_uri is not None, "Model hdfs path not found"

    def test_1_create_instance(self, test_org, test_space, space_users_clients, class_context):
        self.__class__.client = space_users_clients["developer"]
        step("Create scoring engine instance")
        self.__class__.instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.SCORING_ENGINE,
            service_plan_name=ServicePlan.SIMPLE_ATK,
            params={"uri": self.atk_model_uri},
            client=self.client,
            context=class_context
        )
        step("Check instance is on the instance list")
        instances_list = ServiceInstance.api_get_list(test_space.guid, client=self.client)
        assert self.instance in instances_list, "Scoring Engine was not found on the instance list"

    def test_2_check_service_bindings(self):
        step("Check scoring engine has correct bindings")
        validator = ApplicationStackValidator(self.instance)
        validator.validate(expected_bindings=self.expected_se_bindings)
        self.__class__.se_app = validator.application

    def test_3_check_request_to_se_application(self):
        step("Check that Scoring Engine app responds to an HTTP request")
        url = "http://{}/v1/score?data=10.0,1.5,200.0".format(self.se_app.urls[0])
        headers = {"Accept": "text/plain", "Content-Types": "text/plain; charset=UTF-8"}
        response = requests.post(url, data="", headers=headers)
        assert response.text == "-1.0", "Scoring engine response was wrong"

    def test_4_create_service_key(self, test_space):
        step("Check that the instance exists in summary and has no keys")
        summary = ServiceInstance.api_get_keys(test_space.guid, client=self.client)
        assert self.instance in summary, "Instance not found in summary"
        assert summary[self.instance] == [], "There are keys for the instance"
        step("Create a key for the scoring engine instance and check it")
        self.__class__.instance_key = ServiceKey.api_create(self.instance.guid, client=self.client)
        summary = ServiceInstance.api_get_keys(test_space.guid)
        assert self.instance_key in summary[self.instance], "Key not found"

    def test_5_delete_service_key(self, test_space):
        step("Delete service key")
        self.instance_key.api_delete(client=self.client)
        step("Check the key is no longer in summary")
        summary = ServiceInstance.api_get_keys(test_space.guid, client=self.client)
        assert summary[self.instance] == [], "There are keys for the instance"

    def test_6_delete_instance(self, test_space):
        self.instance.api_delete(client=self.client)
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert self.instance not in instances, "Scoring engine instance was not deleted"


@priority.low
class TestScoringEngineUnauthorizedUsers:
    unauthorized_roles = ("manager", "auditor")

    @pytest.mark.parametrize("user_role", unauthorized_roles)
    def test_cannot_create_scoring_engine(self, test_org, test_space, space_users_clients, model_hdfs_path, user_role):
        step("Check that unauthorized user cannot create scoring engine")
        client = space_users_clients[user_role]
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_FORBIDDEN,
                                                ServiceCatalogHttpStatus.MSG_FORBIDDEN,
                                                ServiceInstance.api_create_with_plan_name,
                                                org_guid=test_org.guid, space_guid=test_space.guid,
                                                service_label=ServiceLabels.SCORING_ENGINE,
                                                service_plan_name=ServicePlan.SIMPLE_ATK,
                                                params={"uri": model_hdfs_path}, client=client)
