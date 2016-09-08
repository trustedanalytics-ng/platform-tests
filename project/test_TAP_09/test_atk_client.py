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

import pytest

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import TapComponent as TAP, ServiceLabels, ServicePlan
from modules.markers import incremental, long, priority
from modules.service_tools.atk import ATKtools
from modules.tap_object_model import DataSet, ServiceInstance, ServiceOffering, Transfer
from modules.tap_logger import step
from modules.test_names import generate_test_object_name, escape_hive_name

logged_components = (TAP.atk, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.service_exposer)]


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - ATK as an app??")
@incremental
@priority.high
class TestAtk:

    atk_virtualenv = None
    atk_url = None
    data_set_hdfs_path = None
    transfer_title = generate_test_object_name()

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def atk_virtualenv(cls, request, test_org):
        cls.atk_virtualenv = ATKtools("atk_virtualenv")
        cls.atk_virtualenv.create()

        def fin():
            try:
                cls.atk_virtualenv.teardown(atk_url=cls.atk_url, org=test_org)
            except:
                pass
        request.addfinalizer(fin)

    def test_0_create_atk_instance(self, class_context, test_org, test_space, add_admin_to_test_org):
        step("Check that atk service is available in Marketplace")
        marketplace = ServiceOffering.get_list()
        atk_service = next((s for s in marketplace if s.label == ServiceLabels.ATK), None)
        assert atk_service is not None, "No atk service found in marketplace."
        step("Create atk service instance")

        atk_instance_name = generate_test_object_name()
        atk_instance = ServiceInstance.api_create_with_plan_name(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.ATK,
            name=atk_instance_name,
            service_plan_name=ServicePlan.SIMPLE_ATK
        )

        validator = ApplicationStackValidator(atk_instance)
        validator.validate()
        self.__class__.atk_url = validator.application.urls[0]

    def test_1_install_atk_client(self):
        step("Install atk client package")
        self.atk_virtualenv.pip_install(ATKtools.get_atk_client_url(self.atk_url))

    def test_2_check_atk_client_connection(self):
        step("Run atk connection test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "atk_client_connection_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url)

    @pytest.mark.bugs("DPNG-2010 Cannot get JDBC connection when publishing dataset to Hive")
    def test_3_create_data_set_and_publish_it_in_hive(self, class_context, test_org, test_data_urls):
        step("Create transfer and check it's finished")
        transfer = Transfer.api_create(class_context, source=test_data_urls.test_transfer.url, org_guid=test_org.guid,
                                       title=self.transfer_title)
        transfer.ensure_finished()
        step("Publish in hive the data set created based on the submitted transfer")
        data_set = DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=self.transfer_title)
        data_set.api_publish()
        self.__class__.data_set_hdfs_path = ATKtools.dataset_uri_to_atk_uri(data_set.target_uri)

    @long
    @pytest.mark.bugs("kerberos: DPNG-4525", "non-kerberos: DPNG-5171")
    def test_4_frame_csv_file(self):
        step("Run atk csv file test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "csv_file_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--target_uri": self.data_set_hdfs_path})

    def test_5_simple_hive_query(self, test_org):
        step("Run atk connection test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_simple_query_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--database-name": escape_hive_name(test_org.guid),
                                                      "--table-name": self.transfer_title})

    def test_6_export_to_hive(self, test_org):
        step("Run atk export to hive test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_export_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--database-name": escape_hive_name(test_org.guid),
                                                      "--table-name": self.transfer_title})

    def test_7_hive_table_manipulation(self, test_org):
        step("Run atk table manipulation test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_table_manipulation_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--database-name": escape_hive_name(test_org.guid),
                                                      "--table-name": self.transfer_title})
