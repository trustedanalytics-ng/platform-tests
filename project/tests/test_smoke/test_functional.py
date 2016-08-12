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

from modules.file_utils import generate_csv_file
from modules.constants import TapComponent as TAP, Urls
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, KubernetesCluster, Organization, ServiceInstance, Space, Transfer, User
from modules.tap_object_model.flows import onboarding
import tests.fixtures.assertions as assertions


logged_components = (TAP.user_management, TAP.auth_gateway, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser,
                     TAP.data_catalog, TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker,
                     TAP.hbase_broker, TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker,
                     TAP.zookeeper_broker, TAP.zookeeper_wssb_broker)
pytestmark = [priority.high]


@pytest.mark.components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
def test_create_and_delete_organization(context):
    """Create and Delete Organization"""
    step("Create organization")
    test_org = Organization.api_create(context)
    step("Check that organization is on the list")
    orgs = Organization.api_get_list()
    assert test_org in orgs

    step("Delete organization")
    test_org.api_delete()
    step("Check that the organization is not on the list")
    assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)


@pytest.mark.components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
def test_onboarding(context):
    """Test Onboarding"""
    step("Onboard new user")
    test_user, test_org = onboarding.onboard(context, check_email=False)
    step("Check that user is created")
    users = User.cf_api_get_all_users()
    assert test_user in users
    step("Check that organization is created")
    org_list = Organization.api_get_list()
    assert test_org in org_list

@pytest.mark.components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
def test_add_new_user_to_and_delete_from_org(core_org, context):
    """Add New User to and Delete from Organization"""
    step("Add new user to organization")
    test_user, test_org = onboarding.onboard(context, check_email=False)
    test_user.api_add_to_organization(core_org.guid, roles=User.ORG_ROLES["manager"],)
    step("Check that the user is added")
    users = User.api_get_list_via_organization(org_guid=core_org.guid)
    assert test_user in users
    step("Delete the user from the organization")
    test_user.api_delete_from_organization(org_guid=core_org.guid)
    step("Check that the user is in the organization")
    users = User.api_get_list_via_organization(org_guid=core_org.guid)
    assert test_user not in users


@pytest.mark.components(TAP.user_management)
def test_create_and_delete_space(core_org):
    """Create and Delete Space"""
    step("Create new space")
    test_space = Space.api_create(org=core_org)
    step("Check that the space was created")
    spaces = Space.api_get_list()
    assert test_space in spaces
    step("Delete the space")
    test_space.api_delete()
    step("Check that the space was deleted")
    assertions.assert_not_in_with_retry(test_space, Space.api_get_list)


@pytest.mark.components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
def test_add_new_user_to_and_delete_from_space(core_org, core_space, context):
    """Add New User to and Delete from Space"""
    step("Add new user to space")
    test_user, test_org = onboarding.onboard(context, check_email=False)
    test_user.api_add_to_space(core_space.guid, core_org.guid, roles=User.SPACE_ROLES["manager"])
    step("Check that the user is added")
    users = User.api_get_list_via_space(space_guid=core_space.guid)
    assert test_user in users
    step("Remove the user from space")
    test_user.api_delete_from_space(space_guid=core_space.guid)
    step("Check that the user was deleted")
    users = User.api_get_list_via_space(space_guid=core_space.guid)
    assert test_user not in users


def transfer_flow(transfer, core_org):
    step("Check that the transfer is finished")
    transfer.ensure_finished()
    step("Check that the transfer is on the list")
    transfers = Transfer.api_get_list(org_guid_list=[core_org.guid])
    assert transfer in transfers

    step("Get data set matching to transfer")
    data_set = DataSet.api_get_matching_to_transfer(org=core_org, transfer_title=transfer.title)

    step("Delete the data set")
    data_set.api_delete()
    step("Check that the data set was deleted")
    data_sets = DataSet.api_get_list(org_list=[core_org])
    assert data_set not in data_sets

    step("Delete the transfer")
    transfer.api_delete()
    step("Check that the transfer was deleted")
    transfers = Transfer.api_get_list(org_guid_list=[core_org.guid])
    assert transfer not in transfers


@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.hdfs_downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_link(core_org, context):
    """Create and Delete Transfer from Link"""
    step("Create a transfer")
    transfer = Transfer.api_create(context, category="other", source=Urls.test_transfer_link, org_guid=core_org.guid)
    transfer_flow(transfer, core_org)


@pytest.mark.components(TAP.das, TAP.data_catalog, TAP.hdfs_downloader, TAP.metadata_parser)
def test_add_and_delete_transfer_from_file(core_org, context):
    """Create and Delete Transfer from File"""
    step("Generate a test csv file")
    file_path = generate_csv_file(column_count=10, row_count=100)
    step("Create a transfer by file upload")
    transfer = Transfer.api_create_by_file_upload(context, category="health", org_guid=core_org.guid, file_path=file_path)
    transfer_flow(transfer, core_org)


@long
@pytest.mark.components(TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker, TAP.service_catalog,
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


@long
@pytest.mark.components(TAP.demiurge, TAP.kubernetes_broker)
def test_create_and_delete_kubernetes_service_instances(core_org, core_space, context, kubernetes_marketplace):
    service_type = kubernetes_marketplace[0]
    plan = kubernetes_marketplace[1]

    step("Create instance {} {}".format(service_type.label, plan["name"]))
    instance = ServiceInstance.api_create(context=context, org_guid=core_org.guid, space_guid=core_space.guid,
                                          service_label=service_type.label, service_plan_guid=plan["guid"])
    step("Check that the cluster was created")
    KubernetesCluster.demiurge_api_get(name=core_org.guid)
    step("Check that the instance was created")
    instance.ensure_created()
    step("Delete the instance")
    instance.api_delete()
    step("Check that the instance was deleted")
    instances = ServiceInstance.api_get_list(space_guid=core_space.guid, service_type_guid=service_type.guid)
    assert instance not in instances
