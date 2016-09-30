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
from modules.constants import TapComponent as TAP, Urls
from modules.constants.http_status import PlatformTestsHttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.file_utils import generate_csv_file
from modules.http_client import HttpMethod
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import long, priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import Application, DataSet, Organization, ServiceInstance, Transfer, User
from modules.tap_object_model import ServiceType
from modules.tap_object_model import TestSuite
from modules.tap_object_model.flows import onboarding


logged_components = (TAP.user_management, TAP.auth_gateway, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser,
                     TAP.data_catalog, TAP.service_catalog, TAP.gearpump_broker,
                     TAP.hbase_broker, TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker,
                     TAP.zookeeper_broker, TAP.zookeeper_wssb_broker, TAP.platform_tests)
pytestmark = [priority.high]


def test_login():
    entities = ServiceType.api_get_catalog()
    assert entities is not None


@pytest.fixture(scope="function")
def sample_app(sample_python_app, sample_java_app):
    return {
        "sample_python_app": sample_python_app,
        "sample_java_app": sample_java_app
    }


@pytest.mark.skip(reason="Not implemented for TAP NG yet")
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


@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_onboarding(context):
    """Test Onboarding"""
    step("Onboard new user")
    test_user = onboarding.onboard(context, check_email=False)
    step("Check that user is created")
    users = User.get_all_users()
    assert test_user in users


@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_add_new_user_to_and_delete_from_org(core_org, context):
    """Add New User to and Delete from Organization"""
    step("Add new user to organization")
    test_user = onboarding.onboard(context, check_email=False)
    test_user.add_to_organization(core_org.guid, role=User.ORG_ROLE["admin"])
    step("Check that the user is added")
    users = User.get_list_in_organization(org_guid=core_org.guid)
    assert test_user in users
    step("Delete the user from the organization")
    test_user.delete_from_organization(org_guid=core_org.guid)
    step("Check that the user is in the organization")
    users = User.get_list_in_organization(org_guid=core_org.guid)
    assert test_user not in users


@pytest.mark.skip(reason="Not implemented for TAP NG yet")
def transfer_flow(transfer, core_org):
    step("Check that the transfer is finished")
    transfer.ensure_finished()
    step("Check that the transfer is on the list")
    transfers = Transfer.api_get_list(org_guid_list=[core_org.guid])
    assert transfer in transfers
    step("Get data set matching to transfer")
    data_set = DataSet.api_get_matching_to_transfer(org_guid=core_org.guid, transfer_title=transfer.title)

    step("Delete the data set")
    data_set.api_delete()
    step("Check that the data set was deleted")
    data_sets = DataSet.api_get_list(org_guid_list=[core_org.guid])
    assert data_set not in data_sets

    step("Delete the transfer")
    transfer.api_delete()
    step("Check that the transfer was deleted")
    transfers = Transfer.api_get_list(org_guid_list=[core_org.guid])
    assert transfer not in transfers


@pytest.mark.skip(reason="Not implemented for TAP NG yet")
@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.hdfs_downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_link(core_org, context):
    """Create and Delete Transfer from Link"""
    step("Create a transfer")
    transfer = Transfer.api_create(context, category="other", source=Urls.test_transfer_link, org_guid=core_org.guid)
    transfer_flow(transfer, core_org)


@pytest.mark.skip(reason="Not implemented for TAP NG yet")
@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.hdfs_downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_file(core_org, context):
    """Create and Delete Transfer from File"""
    step("Generate a test csv file")
    file_path = generate_csv_file(column_count=10, row_count=100)
    step("Create a transfer by file upload")
    transfer = Transfer.api_create_by_file_upload(context, category="health", org_guid=core_org.guid,
                                                  file_path=file_path)
    transfer_flow(transfer, core_org)


@long
@pytest.mark.skip(reason="Not implemented for TAP NG yet")
@pytest.mark.components(TAP.gearpump_broker, TAP.hbase_broker, TAP.service_catalog,
                        TAP.smtp_broker, TAP.kafka_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                        TAP.zookeeper_wssb_broker)
def test_create_and_delete_marketplace_service_instances(core_org, core_space, context,
                                                         non_parametrized_marketplace_services):
    """Create and Delete Marketplace Service Instance"""
    service_type = non_parametrized_marketplace_services[0]
    plan = non_parametrized_marketplace_services[1]

    step("Create instance {} {}".format(service_type.label, plan["name"]))
    instance = ServiceInstance.api_create(context=context, org_guid=core_org.guid, space_guid=core_space.guid,
                                          service_label=service_type.label, service_plan_guid=plan["guid"])
    step("Check that the instance was created")
    instance.ensure_created()
    step("Delete the instance")
    instance.api_delete()
    step("Check that the instance was deleted")
    instances = ServiceInstance.api_get_list(space_guid=core_space.guid, service_type_guid=service_type.guid)
    assert instance not in instances


@pytest.mark.parametrize("sample_app_key", ("sample_python_app", "sample_java_app"))
def test_push_sample_app_and_check_response(sample_app, sample_app_key):
    """Push Sample Application and Test Http Response"""
    sample_app = sample_app[sample_app_key]
    client = HttpClientFactory.get(ApplicationConfigurationProvider.get(sample_app.urls[0]))
    step("Check response for HTTP GET to the endpoint")
    response = client.request(method=HttpMethod.GET, path="", timeout=10, raw_response=True)
    assert response is not None
    assert response.status_code == 200


@pytest.mark.skip(reason="Not implemented for TAP NG yet")
@pytest.mark.components(TAP.atk)
def test_connect_to_atk_from_jupyter_using_default_atk_client(context, request, core_space, test_space, test_org,
                                                              admin_user):
    """Connect to Atk from Jupyter using Default Atk Client"""
    step("Get atk app from core space")
    atk_app = next((app for app in Application.cf_api_get_list_by_space(core_space.guid)
                    if app.name == "atk"), None)
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


@pytest.mark.skip(reason="Not implemented for TAP NG yet")
@pytest.mark.components(TAP.platform_tests)
def test_start_tests_or_get_suite_in_progress():
    """Start Tests or get Suite in Progress"""
    step("Start tests")
    try:
        new_test = TestSuite.api_create()
        step("New test suite has been started")
        suite_id = new_test.suite_id
        assert new_test.state == TestSuite.IN_PROGRESS, "New suite state is {}".format(new_test.state)
    except UnexpectedResponseError as e:
        step("Another suite is already in progress")
        assert e.status == PlatformTestsHttpStatus.CODE_TOO_MANY_REQUESTS
        assert PlatformTestsHttpStatus.MSG_RUNNER_BUSY in e.error_message
        step("Get list of test suites and retrieve suite in progress")
        tests = TestSuite.api_get_list()
        test_in_progress = next((t for t in tests if t.state == TestSuite.IN_PROGRESS), None)
        assert test_in_progress is not None, "Cannot create suite, although no other suite is in progress"
        suite_id = test_in_progress.suite_id
    step("Get suite details")
    created_test_results = TestSuite.api_get_test_suite_results(suite_id)
    assert created_test_results is not None
