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
import re

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

    FILE_CONTENT = "simple content"
    FILE_NAME = "test_file"

    @classmethod
    @pytest.fixture(scope="class")
    def hdfs_instance(cls, class_context, request, test_org, test_space):
        step("Create Hdfs encrypted instance.")
        instance = ServiceInstance.api_create_with_plan_name(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.HDFS,
            service_plan_name=ServicePlan.ENCRYPTED
        )
        return instance

    @classmethod
    @pytest.fixture(scope="class")
    def hdfs_client(cls):
        return Hdfs()

    def test_0_get_zone_path(self, hdfs_instance, hdfs_client):
        step("List hdfs crypt zones.")
        output = hdfs_client.list_zones()
        match = re.search(r"\S*{}\S*".format(hdfs_instance.guid), output, re.MULTILINE)
        assert match is not None, "No encryption zone for hdfs instance"
        self.__class__.hdfs_path = match.group(0)

    def test_1_put_file(self, hdfs_client):
        step("Put file in hdfs")
        hdfs_client.put("{}/".format(self.hdfs_path), self.FILE_CONTENT)

    def test_2_read_file(self, hdfs_client):
        step("Read file from hdfs")
        output = hdfs_client.cat("{}/{}".format(self.hdfs_path, self.FILE_NAME))
        assert self.FILE_CONTENT == output
