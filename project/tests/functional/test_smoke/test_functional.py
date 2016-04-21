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

from modules.api_client import PlatformApiClient
from modules.file_utils import generate_csv_file
from modules.constants import PARAMETRIZED_SERVICE_INSTANCES, TapComponent as TAP, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, mark, priority
from modules.tap_object_model import DataSet, Organization, ServiceInstance, ServiceType, Space, Transfer, User


@log_components(TAP.user_management, TAP.auth_gateway, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser,
                TAP.data_catalog, TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker,
                TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                TAP.zookeeper_wssb_broker)
class FunctionalSmokeTests(TapTestCase):

    @classmethod
    def setUpClass(cls):
        cls.step("Get reference organization and space")
        cls.ref_org, cls.ref_space = Organization.get_ref_org_and_space()

    @priority.high
    def test_0_test_admin_can_login_to_platform(self):
        PlatformApiClient.get_admin_client()

    @priority.high
    @components(TAP.user_management, TAP.auth_gateway)
    def test_create_and_delete_organization(self):
        self.step("Create organization")
        test_org = Organization.api_create()
        self.step("Check that organization is on the list")
        orgs = Organization.api_get_list()
        self.assertIn(test_org, orgs)
        self.step("Delete organization")
        test_org.api_delete()
        self.step("Check that the organization is not on the list")
        self.assertNotInWithRetry(test_org, Organization.api_get_list)

    @priority.high
    @components(TAP.user_management, TAP.auth_gateway)
    def test_onboarding(self):
        self.step("Onboard new user")
        test_user, test_org = User.api_onboard_without_email()
        self.step("Check that user is created")
        users = User.cf_api_get_all_users()
        self.assertIn(test_user, users)
        self.step("Check that organization is created")
        orgs = Organization.api_get_list()
        self.assertIn(test_org, orgs)

    @priority.high
    @components(TAP.user_management, TAP.auth_gateway)
    def test_add_new_user_to_and_delete_from_org(self):
        self.step("Add new user to organization")
        test_user, test_org = User.api_onboard_without_email()
        test_user.api_add_to_organization(self.ref_org.guid, roles=User.ORG_ROLES["manager"],)

        self.step("Check that the user is added")
        users = User.api_get_list_via_organization(org_guid=self.ref_org.guid)
        self.assertIn(test_user, users)
        self.step("Delete the user from the organization")
        test_user.api_delete_from_organization(org_guid=self.ref_org.guid)
        self.step("Check that the user is in the organization")
        users = User.api_get_list_via_organization(org_guid=self.ref_org.guid)
        self.assertNotIn(test_user, users)

    @priority.high
    @components(TAP.user_management)
    def test_create_and_delete_space(self):
        self.step("Create new space")
        test_space = Space.api_create(org=self.ref_org)
        self.step("Check that the space was created")
        spaces = Space.api_get_list()
        self.assertIn(test_space, spaces)
        self.step("Delete the space")
        test_space.api_delete()
        self.step("Check that the space was deleted")
        self.assertNotInWithRetry(test_space, Space.api_get_list)

    @priority.high
    @components(TAP.user_management, TAP.auth_gateway)
    def test_add_new_user_to_and_delete_from_space(self):
        self.step("Add new user to space")
        test_user, test_org = User.api_onboard_without_email()
        test_user.api_add_to_space(self.ref_space.guid, self.ref_org.guid, roles=User.SPACE_ROLES["manager"])

        self.step("Check that the user is added")
        users = User.api_get_list_via_space(space_guid=self.ref_space.guid)
        self.assertIn(test_user, users)
        self.step("Remove the user from space")
        test_user.api_delete_from_space(space_guid=self.ref_space.guid)
        self.step("Check that the user was deleted")
        users = User.api_get_list_via_space(space_guid=self.ref_space.guid)
        self.assertNotIn(test_user, users)

    @priority.high
    @components(TAP.das, TAP.hdfs_downloader, TAP.metadata_parser, TAP.data_catalog)
    def test_add_and_delete_transfer_from_link(self):
        self.step("Create a transfer and check it has finished")
        transfer = Transfer.api_create(category="other", source=Urls.test_transfer_link, org_guid=self.ref_org.guid)
        transfer.ensure_finished()
        self.step("Check that the transfer is on the list")
        transfers = Transfer.api_get_list(org_guid_list=[self.ref_org.guid])
        self.assertIn(transfer, transfers)
        self.step("Get data set matching to transfer")
        data_set = DataSet.api_get_matching_to_transfer(org_list=[self.ref_org], transfer_title=transfer.title)
        self.step("Delete the data set")
        data_set.api_delete()
        self.step("Check that the data set was deleted")
        data_sets = DataSet.api_get_list(org_list=[self.ref_org])
        self.assertNotIn(data_set, data_sets)
        self.step("Delete the transfer")
        transfer.api_delete()
        self.step("Check that the transfer was deleted")
        transfers = Transfer.api_get_list(org_guid_list=[self.ref_org.guid])
        self.assertNotIn(transfer, transfers)

    @priority.high
    @components(TAP.das, TAP.hdfs_uploader, TAP.metadata_parser, TAP.data_catalog)
    def test_add_and_delete_transfer_from_file(self):
        self.step("Generate a test csv file")
        file_path = generate_csv_file(column_count=10, row_count=100)
        self.step("Create a transfer and check it has finished")
        transfer = Transfer.api_create_by_file_upload(category="health", org_guid=self.ref_org.guid, file_path=file_path)
        transfer.ensure_finished()
        self.step("Check that the transfer is on the list")
        transfers = Transfer.api_get_list(org_guid_list=[self.ref_org.guid])
        self.assertIn(transfer, transfers)
        self.step("Get data set for the transfer")
        data_set = DataSet.api_get_matching_to_transfer(org_list=[self.ref_org], transfer_title=transfer.title)
        self.step("Delete the data set")
        data_set.api_delete()
        self.step("Check that the data set was deleted")
        data_sets = DataSet.api_get_list(org_list=[self.ref_org])
        self.assertNotIn(data_set, data_sets)
        self.step("Delete the transfer")
        transfer.api_delete()
        self.step("Check that the transfer was deleted")
        transfers = Transfer.api_get_list(org_guid_list=[self.ref_org.guid])
        self.assertNotIn(transfer, transfers)

    @mark.long
    @priority.high
    @components(TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker, TAP.hdfs_broker,
                TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker, TAP.zookeeper_wssb_broker)
    def test_create_and_delete_marketplace_service_instances(self):
        self.step("Get list of services in marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=self.ref_space.guid)
        marketplace = [s for s in marketplace if s.label not in PARAMETRIZED_SERVICE_INSTANCES]
        for service in marketplace:
            for plan in service.service_plans:
                with self.subTest(service=service.label, plan=plan["name"]):
                    self.step("Create instance")
                    instance = ServiceInstance.api_create(org_guid=self.ref_org.guid, space_guid=self.ref_space.guid,
                                                          service_label=service.label, service_plan_guid=plan["guid"])
                    self.step("Check that the instance was created")
                    instances = ServiceInstance.api_get_list(space_guid=self.ref_space.guid,
                                                             service_type_guid=service.guid)
                    self.assertIn(instance, instances)
                    self.step("Delete the instance")
                    instance.api_delete()
                    self.step("Check that the instance was deleted")
                    instances = ServiceInstance.api_get_list(space_guid=self.ref_space.guid,
                                                             service_type_guid=service.guid)
                    self.assertNotIn(instance, instances)
