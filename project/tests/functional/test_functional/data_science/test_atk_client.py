#
# Copyright (c) 2015-2016 Intel Corporation
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

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import Priority, TapComponent as TAP, ServiceLabels, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, incremental
from modules.service_tools.atk import ATKtools
from modules.tap_object_model import DataSet, Organization, ServiceInstance, ServiceType, Space, Transfer, User
from modules.test_names import get_test_name


@log_components()
@incremental(Priority.high)
@components(TAP.atk, TAP.dataset_publisher, TAP.application_broker, TAP.service_catalog, TAP.das, TAP.hdfs_downloader,
            TAP.metadata_parser)
class Atk(TapTestCase):
    ATK_PLAN_NAME = "Simple"
    atk_virtualenv = None
    atk_url = None
    data_set_hdfs_path = None

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)
        cls.step("Add admin to the test space")
        admin_user = User.get_admin()
        admin_user.api_add_to_space(space_guid=cls.test_space.guid, org_guid=cls.test_org.guid,
                                    roles=User.SPACE_ROLES["developer"])
        cls.step("Create virtualenv for atk client")
        cls.atk_virtualenv = ATKtools("atk_virtualenv")
        cls.atk_virtualenv.create()
        cls.transfer_title = get_test_name()

    @classmethod
    def tearDownClass(cls):
        """DPNG-6117 ATK teardown failed during api-tests run"""
        cls.atk_virtualenv.teardown(atk_url=cls.atk_url, org=cls.test_org)
        super().tearDownClass()

    def test_0_check_atk_uaac_credentials(self):
        self.step("Check if atk has correct credentials and is able to download uaac token")
        ATKtools.check_uaac_token()

    def test_1_create_atk_instance(self):
        self.step("Check that atk service is available in Marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        atk_service = next((s for s in marketplace if s.label == ServiceLabels.ATK), None)
        self.assertIsNotNone(atk_service, msg="No atk service found in marketplace.")
        self.step("Create atk service instance")
        atk_instance_name = get_test_name()
        atk_instance = ServiceInstance.api_create(
            org_guid=self.test_org.guid,
            space_guid=self.test_space.guid,
            service_label=ServiceLabels.ATK,
            name=atk_instance_name,
            service_plan_name=self.ATK_PLAN_NAME
        )
        validator = ApplicationStackValidator(self, atk_instance)
        validator.validate()
        self.__class__.atk_url = validator.application.urls[0]

    def test_2_install_atk_client(self):
        self.step("Install atk client package")
        self.atk_virtualenv.pip_install(ATKtools.get_atk_client_url(self.atk_url))

    def test_3_check_atk_client_connection(self):
        self.step("Run atk connection test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "atk_client_connection_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url)

    def test_4_create_data_set_and_publish_it_in_hive(self):
        """DPNG-2010 Cannot get JDBC connection when publishing dataset to Hive"""
        self.step("Create transfer and check it's finished")
        Transfer.api_create(source=Urls.test_transfer_link, org_guid=self.test_org.guid, title=self.transfer_title).ensure_finished()
        self.step("Publish in hive the data set created based on the submitted transfer")
        data_set = DataSet.api_get_matching_to_transfer(org_list=[self.test_org], transfer_title=self.transfer_title)
        data_set.api_publish()
        self.__class__.data_set_hdfs_path = data_set.target_uri

    def test_5_frame_csv_file(self):
        """kerberos: DPNG-4525, non-kerberos: DPNG-5171"""
        self.step("Run atk csv file test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "csv_file_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--target_uri": self.data_set_hdfs_path})

    def test_6_simple_hive_query(self):
        self.step("Run atk connection test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_simple_query_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--organization": self.test_org.name,
                                                      "--transfer": self.transfer_title})

    def test_7_export_to_hive(self):
        self.step("Run atk export to hive test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_export_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--organization": self.test_org.name,
                                                      "--transfer": self.transfer_title})

    def test_8_hive_table_manipulation(self):
        self.step("Run atk table manipulation test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_table_manipulation_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--organization": self.test_org.name,
                                                      "--transfer": self.transfer_title})
