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

from modules.constants import TapComponent as TAP
from modules.tap_object_model import Platform
from modules.markers import priority
from modules.tap_object_model.buildpack import Buildpack
from modules.tap_logger import step
from tests.fixtures.assertions import assert_unordered_list_equal

logged_components = (TAP.platform_operations, TAP.metrics_provider)
pytestmark = [pytest.mark.components(TAP.platform_operations, TAP.metrics_provider)]


@pytest.mark.skip(reason="Not yet adjusted to new TAP")
class TestBuildpacks(object):

    def get_buildpack_list(self, bdict):
        """
        create buildpack list from platform metrics infos
        :return: list of buildpacks
        """
        buildpacks = []
        for data in bdict:
            buildpack = Buildpack(name=data["entity"]["name"], guid=data["metadata"]["guid"], url=None,
                                  filename=data["entity"]["filename"], position=data["entity"]["position"],
                                  enabled=data["entity"]["enabled"], locked=data["entity"]["locked"])
            buildpacks.append(buildpack)
        return buildpacks

    @priority.low
    def test_buildpack_info(self):
        step("Get buildpack info from platform metrics")
        platform = Platform()
        platform.retrieve_metrics(refresh=False)
        tap_bps = self.get_buildpack_list(platform.metrics.buildpacks_data)
        step("Get buildpack info from cloud foundry")
        cf_bps = Buildpack.cf_api_get_list()
        step("Compare two lists")
        assert_unordered_list_equal(tap_bps, cf_bps, "CF buildpacks info differs from TAP buildpacks info")
