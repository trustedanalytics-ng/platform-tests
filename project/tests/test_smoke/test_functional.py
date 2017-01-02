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

from modules.constants import Guid, ServiceLabels, TapComponent as TAP
from modules.constants.http_status import PlatformTestsHttpStatus
from modules.constants.model_metadata import MODEL_METADATA
from modules.exceptions import UnexpectedResponseError
from modules.file_utils import generate_csv_file
from modules.http_client import HttpMethod
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer, User, TestRun, ServiceInstance, Metrics, Organization
from modules.tap_object_model.flows import onboarding
from modules.tap_object_model.platform_tests import TestSuite
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from tap_component_config import offerings_as_parameters
from tests.fixtures.assertions import assert_dict_values_set

logged_components = (TAP.user_management, TAP.auth_gateway, TAP.das, TAP.downloader, TAP.metadata_parser,
                     TAP.data_catalog, TAP.service_catalog, TAP.gearpump_broker,
                     TAP.hbase_broker, TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker,
                     TAP.zookeeper_broker, TAP.zookeeper_wssb_broker, TAP.platform_tests)
pytestmark = [priority.high]

expected_metrics_keys = ["apps_running", "apps_down", "users_org", "service_usage", "memory_usage_org", "cpu_usage_org",
                         "private_datasets", "public_datasets"]
not_tested_offerings = [ServiceLabels.ELASTICSEARCH17, ServiceLabels.GEARPUMP, ServiceLabels.H2O, ServiceLabels.HBASE,
                        ServiceLabels.HDFS, ServiceLabels.HIVE, ServiceLabels.INFLUX_DB_110, ServiceLabels.JUPYTER,
                        ServiceLabels.ORIENT_DB, ServiceLabels.RABBIT_MQ, ServiceLabels.SCORING_ENGINE,
                        ServiceLabels.SCORING_PIPELINES, ServiceLabels.ZOOKEEPER]
filtered_offerings_as_parameters = list(filter(lambda x: x[0] not in not_tested_offerings, offerings_as_parameters))


def test_login():
    """
    <b>Description:</b>
    Checks if login to platform works.

    <b>Input data:</b>
    1. User name.
    2. Password.

    <b>Expected results:</b>
    Test passes when user was logged successfully into platform.

    <b>Steps:</b>
    1. Log into platform.
    2. Get organization list and verify that it's not None.
    """
    orgs_list = Organization.get_list()
    assert orgs_list is not None


@pytest.fixture(params=['sample_python_app', 'sample_java_app', 'sample_go_app'])
def sample_app(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture(params=['app_bound_mysql', 'app_bound_mongodb', 'app_bound_psql'])
def sample_db_app(request):
    return request.getfuncargvalue(request.param)


@pytest.mark.components(TAP.metrics_grafana)
@pytest.mark.bugs("DPNG-13789 Values for memory_usage and cpu_usage for organization are not passed by Grafana")
def test_dashboard_metrics():
    """
    <b>Description:</b>
    Checks if platform returns following Dashboard Metrics: "apps_running", "apps_down", "users_org", "service_usage",
    "memory_usage_org", "cpu_usage_org", "private_datasets", "public_datasets".

    <b>Input data:</b>
    No input data.

    <b>Expected results:</b>
    Test passes when Grafana returns all expected metrics i.e. "apps_running", "apps_down", "users_org",
    "service_usage", "memory_usage_org", "cpu_usage_org", "private_datasets", "public_datasets".

    <b>Steps:</b>
    1. Get metrics from Grafana.
    2. Verify that Grafana returned following metrics: "apps_running", "apps_down", "users_org", "service_usage",
    "memory_usage_org", "cpu_usage_org", "private_datasets", "public_datasets".
    """
    step("Get metrics from Grafana")
    dashboard_metrics = Metrics.from_grafana()
    step("Check if all expected metrics returned")
    assert_dict_values_set(vars(dashboard_metrics), expected_metrics_keys)


@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_onboarding(context, test_org):
    """
    <b>Description:</b>
    Checks if user can be added to the platform with onboarding functionality.

    <b>Input data:</b>
    1. User email.

    <b>Expected results:</b>
    Test passes when user was successfully added to the platform with onboading functionality.

    <b>Steps:</b>
    1. Onboard new user to the platform.
    2. Get list of all users on the platform.
    3. Verify that the user is present on the platform.
    """
    step("Onboard new user")
    test_user = onboarding.onboard(context=context, org_guid=test_org.guid,
                                   check_email=False)
    step("Check that user is created")
    users = User.get_all_users(test_org.guid)
    assert test_user in users


@pytest.mark.components(TAP.auth_gateway, TAP.user_management)
def test_add_new_user_to_and_delete_from_org(core_org, context):
    """
    <b>Description:</b>
    Checks if admin user can be added and removed from the platform.

    <b>Input data:</b>
    1. User email.

    <b>Expected results:</b>
    Test passes when admin user was successfully added to the platform and removed from it.

    <b>Steps:</b>
    1. Onboard new user to the platform.
    2. Add new user to the default organization.
    3. Verify the user is present in the organization.
    4. Remove the user from the organization.
    5. Verify that the user was removed from the organization.
    """
    step("Add new user to organization")
    test_user = onboarding.onboard(context=context, org_guid=core_org.guid,
                                   check_email=False)
    test_user.add_to_organization(org_guid=core_org.guid, role=User.ORG_ROLE["admin"])
    step("Check that the user is added")
    users = User.get_list_in_organization(org_guid=core_org.guid)
    assert test_user in users
    step("Delete the user from the organization")
    test_user.delete_from_organization(org_guid=core_org.guid)
    step("Check that the user is not in the organization")
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
def test_add_and_delete_transfer_from_link(core_org, context, test_data_urls):
    """
    <b>Description:</b>
    Checks if a file can be downloaded from a link to the platform.

    <b>Input data:</b>
    1. File URL.
    2. Transfer title.
    3. Transfer category.

    <b>Expected results:</b>
    Test passes when a file from link was downloaded to the platform and corresponding transfer and dataset were
    successfully created and removed from the platform.

    <b>Steps:</b>
    1. Create a transfer using csv file.
    2. Check if transfer finished with correct state and verify that it is present on the transfers list.
    3. Check if the transfer has corresponding dataset.
    4. Delete dataset and transfer from the platform.
    5. Verify that transfer and dataset were removed from the platform.
    """
    step("Create a transfer")
    transfer = Transfer.api_create(context, category="other", source=test_data_urls.test_transfer.url,
                                   org_guid=core_org.guid)
    transfer_flow(transfer, core_org)


@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_file(core_org, context):
    """
    <b>Description:</b>
    Checks if a file can be uploaded from disk to the platform.

    <b>Input data:</b>
    1. File name.
    2. Transfer title.
    3. Transfer category.

    <b>Expected results:</b>
    Test passes when a file from disk was uploaded to the platform and corresponding transfer and dataset were
    successfully created and removed from the platform.

    <b>Steps:</b>
    1. Create a transfer using generated csv file.
    2. Check if transfer finished with correct state and verify that it is present on the transfers list.
    3. Check if the transfer has corresponding dataset.
    4. Delete dataset and transfer from the platform.
    5. Verify that transfer and dataset were removed from the platform.
    """
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
@pytest.mark.parametrize("service_label,plan_name", filtered_offerings_as_parameters)
def test_create_and_delete_marketplace_service_instances(context, service_label, plan_name):
    """
    <b>Description:</b>
    Checks if a service instance can be created and deleted from the platform.

    <b>Input data:</b>
    1. Offering names.

    <b>Expected results:</b>
    Test passes when a service instance was successfully created and removed from the platform for every marketplace
    official offering and its plans.

    <b>Steps:</b>
    1. Create service instance of every offering and its plans.
    2. Verify that the service instance is in state RUNNING.
    3. Delete the service instance of an offering.
    4. Verify the service instance was deleted from the platform.
    """
    step("Create instance {} {}".format(service_label, plan_name))
    instance = ServiceInstance.create_with_name(context, offering_label=service_label, plan_name=plan_name)
    step("Check that the instance is running")
    instance.ensure_running()
    step("Stop service instance")
    instance.stop()
    instance.ensure_stopped()
    step("Delete the instance")
    instance.delete()
    step("Check that the instance was deleted")
    instance.ensure_deleted()


@pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
def test_push_sample_app_and_check_response(sample_app):
    """
    <b>Description:</b>
    Checks if sample python and java applications pushed to the platform work.

    <b>Input data:</b>
    1. Application names.
    2. Application gzip paths.
    3. Application manifest paths.

    <b>Expected results:</b>
    Test passes when python and java applications are in RUNNING state and return OK status to HTTP GET request.

    <b>Steps:</b>
    1. Create HTTP client.
    2. Send GET request with the client.
    3. Verify response is not None and response status code equals 200.
    """
    client = HttpClientFactory.get(ApplicationConfigurationProvider.get(sample_app.urls[0]))
    step("Check response for HTTP GET to the endpoint")
    response = client.request(method=HttpMethod.GET, path="", timeout=10, raw_response=True)
    assert response is not None
    assert response.status_code == 200


@pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
def test_push_db_app_and_check_response(sample_db_app):
    """
    <b>Description:</b>
    Checks if application pushed to the platform with postgres or mysql database service bound work.

    <b>Input data:</b>
    1. Application names.
    2. Application gzip paths.
    3. Application manifest paths.

    <b>Expected results:</b>
    Test passes when application with postgres or mysql database service bound are in RUNNING state and returns OK
    status to HTTP GET request.

    <b>Steps:</b>
    1. Create HTTP client.
    2. Send GET request with the client.
    3. Verify response is not None and response status code equals 200.
    """
    client = HttpClientFactory.get(ApplicationConfigurationProvider.get(sample_db_app.urls[0]))
    response = client.request(method=HttpMethod.GET, path="", timeout=10, raw_response=True)
    assert response is not None
    assert response.status_code == 200


@pytest.mark.components(TAP.platform_tests)
def test_get_platform_tests_suites():
    """
    <b>Description:</b>
    Checks if platform tests suites can be retrieved.

    <b>Input data:</b>
    no input data

    <b>Expected results:</b>
    At least one test suite is retrieved with at least one test.

    <b>Steps:</b>
    1. Get test suites.
    2. Verify there is at least one test suite.
    3. Verify there is at least one test in first test suite.
    """
    step("Get list of test suites")
    suites = TestSuite.api_get_test_suites()
    assert len(suites) > 0, "No test suites."
    assert len(suites[0].tests) > 0, "No test in first test suite."


@priority.high
def test_add_new_model_to_organization(context):
    """
    <b>Description:</b>
    Checks if new model can be added to the platform.

    <b>Input data:</b>
    1. Scoring Engine Model.

    <b>Expected results:</b>
    Test passes when model was successfully added to the platform.

    <b>Steps:</b>
    1. Create a model in the organization.
    2. Get list with models on the platform.
    3. Verify the model is on the list.
    """
    step("Add model to organization as admin")
    new_model = ScoringEngineModel.create(context, org_guid=Guid.CORE_ORG_GUID,
                                          **MODEL_METADATA)
    step("Check that the model is on model list")
    models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
    assert new_model in models
