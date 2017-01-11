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
from modules.constants import TapComponent as TAP, ServiceLabels, ServicePlan
from modules.hdfs import Hdfs
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance

logged_components = (TAP.hdfs_broker,)
pytestmark = [pytest.mark.components(TAP.hdfs_broker)]


@incremental
@priority.medium
class TestEncryptedHdfs:

    def test_0_hdfs_encrypted(self, class_context):
        """
        <b>Description:</b>
        Verify if is it possible to create instance of HDFS in plan Encrypted.

        Test create HDFS instance with plan Encrypted and check that instance running.

        <b>Input data:</b>
            HDFS instance

        <b>Expected results:</b>
            HDFS instance with plan Encrypted is created and running.

        <b>Steps:</b>
            1. Create HDFS instance with plan Encrypted
            2. Check that instance is running
        """
        step("Create HDFS instance in plan Plain-Dir")
        self.__class__.instance_hdfs = ServiceInstance.create_with_name(class_context, offering_label=ServiceLabels.HDFS,
                                                                       plan_name=ServicePlan.ENCRYPTED)
        step("Ensure instance is in RUNNING state")
        self.instance_hdfs.ensure_running()

    def test_1_list_zones(self, test_org):
        """
         <b>Description:</b>
            List all encryption zones and verify if instance is present on list.

        <b>Input data:</b>
            HDFS instance

        <b>Expected results:</b>
            HDFS instance is on encryption zones list.

        <b>Steps:</b>
            1. List encryption zones in HDFS
            2. Verify if instance is on list
        """
        org = test_org
        self.__class__.hdfs = Hdfs(org=org)
        zones = self.hdfs.list_zones()
        assert self.instance_hdfs.id in str(zones)

    def test_2_put_file(self, test_org):
        """
         <b>Description:</b>
            Verify if is it possible to put file into HDFS directory.

        <b>Input data:</b>
            HDFS instance
            Sample file

        <b>Expected results:</b>
            It is possible to put file into HDFS directory

        <b>Steps:</b>
            1. Put file into HDFS directory
        """
        step("Put file in hdfs")
        self.__class__.file = self.hdfs.create_sample_file()
        self.hdfs.put(file_path=self.file['name'], service_instance_id=self.instance_hdfs.id)
        paths = self.hdfs.ls(service_instance_id=self.instance_hdfs.id)
        assert self.file['name'] in str(paths)

    def test_3_read_file(self):
        """
        <b>Description:</b>
            Verify if file in HDFS directory is able to read.

        <b>Input data:</b>
            HDFS instance
            Sample file

        <b>Expected resuls:</b>
            It's able to read file in HDFS directory.

        <b>Steps:</b>
            1. Read file from HDFS directory
        """
        step("Read file from hdfs")
        cat = self.hdfs.cat(service_instance_id=self.instance_hdfs.id, file_name=self.file['name'])
        assert self.file['content'] in str(cat)

    @pytest.mark.skip(reason="DPNG-14805 - Cannot remove instance hdfs in plain-dir")
    def test_4_delete_hdfs_service_instance(self):
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
        step("Stop HDFS instance")
        self.instance_hdfs.stop()
        self.instance_hdfs.ensure_stopped()
        step("Delete HDFS instance")
        self.instance_hdfs.delete()
        step("Ensure HDFS instance deleted properly")
        self.instance_hdfs.ensure_deleted()
