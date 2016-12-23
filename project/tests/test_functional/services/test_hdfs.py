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
from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, Organization
from modules.hdfs import Hdfs

logged_components = (TAP.hdfs_broker,)
pytestmark = [pytest.mark.components(TAP.hdfs_broker)]


label = ServiceLabels.HDFS


@incremental
@priority.medium
class TestHdfsPlainDir(object):

    def test_0_hdfs_plain_dir(self, class_context):
        """
        <b>Description:</b>
        Verify if is it possible to create instance of HDFS in plan Plain-Dir.

        Test create HDFS instance with plan Plain-Dir and check that instance running.

        <b>Input data:</b>
            HDFS instance

        <b>Expected results:</b>
            HDFS instance with plan Plain-Dir is created and running.

        <b>Steps:</b>
            1. Create HDFS instance with plan Plain-Dir
            2. Check that instance is running
        """
        step("Create HDFS instance in plan Plain-Dir")
        self.__class__.instance_hdfs = ServiceInstance.create_with_name(class_context, offering_label=ServiceLabels.HDFS,
                                                                        plan_name=ServicePlan.PLAIN_DIR)
        step("Ensure instance is in RUNNING state")
        self.instance_hdfs.ensure_running()

    def test_1_hdfs_check_directory_created(self, test_org):
        """
        <b>Description:</b>
            Verify if HDFS directory is created properly.

        <b>Input data:</b>
            HDFS instance

        <b>Expected results:</b>
            HDFS directory is created with proper location and name.

        <b>Steps</b>
            1. Check that HDFS directory exists with right name
        """
        org = test_org
        self.__class__.hdfs = Hdfs(org)
        step("Check if hdfs directory exists in proper place")
        self.hdfs.check_plain_dir_directory(service_instance_id=self.instance_hdfs.id)

    def test_2_hdfs_check_directory_permissions(self):
        """
        <b>Description:</b>
            Verify if HDFS directory has right permissions.

        <b>Input data:</b>
            HDFS instance
            HDFS directory

        <b>Expected results:</b>
            HDFS directory has proper permissions.

        <b>Steps:</b>
            1. Check HDFS directory permissions
        """
        step("Check if hdfs directory has proper permissions")
        self.hdfs.check_plain_dir_permissions(service_instance_id=self.instance_hdfs.id)

    @pytest.mark.skip("DPNG-13935 Cannot update service instance state to 'DESTROY_REQ' in Catalog: currentState and"
                      " stateToSet cannot be empty")
    def test_3_delete_hdfs_service_instance(self):
        """
        <b>Description:</b>
            Delete HDFS instance and check if it is deleted.

        <b>Input data:</b>
            HDFS instance

        <b>Expected results:</b>
           HDFS instance is deleted.

        <b>Steps:</b>
            1. Delete HDFS instance
            2. Verify if HDFS instance is deleted
        """
        step("Delete HDFS instance")
        self.instance_hdfs.stop()
        self.instance_hdfs.ensure_stopped()
        self.instance_hdfs.delete()
        step("Ensure HDFS instance deleted properly")
        self.instance_hdfs.ensure_deleted()
