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

from modules.constants import TapComponent as TAP, Urls
from modules.constants.http_status import PlatformTestsHttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.file_utils import generate_csv_file
from modules.http_client import HttpMethod
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer, User, ServiceOffering, TestSuite, ServiceInstance
from modules.tap_object_model.flows import onboarding
from tap_component_config import offerings_as_parameters

logged_components = (TAP.user_management, TAP.auth_gateway, TAP.das, TAP.downloader, TAP.metadata_parser,
                     TAP.data_catalog, TAP.service_catalog, TAP.gearpump_broker,
                     TAP.hbase_broker, TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker,
                     TAP.zookeeper_broker, TAP.zookeeper_wssb_broker, TAP.platform_tests)
pytestmark = [priority.high]


def test_login():
    entities = ServiceOffering.get_list()
    assert entities is not None


@pytest.fixture(scope="function")
def sample_app(sample_python_app, sample_java_app):
    return {
        "sample_python_app": sample_python_app,
        "sample_java_app": sample_java_app
    }


@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_onboarding(context):
    """Test Onboarding"""
    step("Onboard new user")
    test_user = onboarding.onboard(context=context, check_email=False)
    step("Check that user is created")
    users = User.get_all_users()
    assert test_user in users


@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_add_new_user_to_and_delete_from_org(core_org, context):
    """Add New User to and Delete from Organization"""
    step("Add new user to organization")
    test_user = onboarding.onboard(context=context, check_email=False)
    test_user.add_to_organization(org_guid=core_org.guid, role=User.ORG_ROLE["admin"])
    step("Check that the user is added")
    users = User.get_list_in_organization(org_guid=core_org.guid)
    assert test_user in users
    step("Delete the user from the organization")
    test_user.delete_from_organization(org_guid=core_org.guid)
    step("Check that the user is in the organization")
    users = User.get_list_in_organization(org_guid=core_org.guid)
    assert test_user not in users


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


@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_link(core_org, context):
    """Create and Delete Transfer from Link"""
    step("Create a transfer")
    transfer = Transfer.api_create(context, category="other", source=Urls.test_transfer_link, org_guid=core_org.guid)
    transfer_flow(transfer, core_org)


@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_file(core_org, context):
    """Create and Delete Transfer from File"""
    step("Generate a test csv file")
    file_path = generate_csv_file(column_count=10, row_count=100)
    step("Create a transfer by file upload")
    transfer = Transfer.api_create_by_file_upload(context, category="health", org_guid=core_org.guid,
                                                  file_path=file_path)
    transfer_flow(transfer, core_org)


@long
@pytest.mark.bugs("DPNG-11638 Creation of some service-instances from Marketplace end with failure")
@pytest.mark.components(TAP.gearpump_broker, TAP.hbase_broker, TAP.service_catalog,
                        TAP.smtp_broker, TAP.kafka_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                        TAP.zookeeper_wssb_broker)
@pytest.mark.parametrize("service_label,plan_name", offerings_as_parameters)
def test_create_and_delete_marketplace_service_instances(context, service_label, plan_name):
    """Create and Delete Marketplace Service Instance"""
    step("Create instance {} {}".format(service_label, plan_name))
    instance = ServiceInstance.create_with_name(context, offering_label=service_label, plan_name=plan_name)
    step("Check that the instance is running")
    instance.ensure_running()
    step("Delete the instance")
    instance.delete()
    step("Check that the instance was deleted")
    instance.ensure_deleted()


@pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
@pytest.mark.parametrize("sample_app_key", ("sample_python_app", "sample_java_app"))
def test_push_sample_app_and_check_response(sample_app, sample_app_key):
    """Push Sample Application and Test Http Response"""
    sample_app = sample_app[sample_app_key]
    client = HttpClientFactory.get(ApplicationConfigurationProvider.get(sample_app.urls[0]))
    step("Check response for HTTP GET to the endpoint")
    response = client.request(method=HttpMethod.GET, path="", timeout=10, raw_response=True)
    assert response is not None
    assert response.status_code == 200


@pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
def test_push_psql_app_check_response(psql_app):
    """Push Sample Application and Test Http Response"""
    client = HttpClientFactory.get(ApplicationConfigurationProvider.get(psql_app.urls[0]))
    response = client.request(method=HttpMethod.GET, path="", timeout=10, raw_response=True)
    assert response is not None
    assert response.status_code == 200


@pytest.mark.skip(reason="DPNG-11944 [api-tests] adjust test_platform_tests to new TAP")
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
