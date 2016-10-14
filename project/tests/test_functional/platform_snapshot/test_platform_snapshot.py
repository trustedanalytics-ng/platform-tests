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
from retry import retry

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import PlatformSnapshot

logged_components = (TAP.platform_snapshot,)
pytestmark = [pytest.mark.components(TAP.platform_snapshot)]


@pytest.mark.skip(reason="DPNG-11945 [api-tests] Adjust test_snapshot tests to new TAP")
class TestSnapshot:

    @retry(AssertionError, tries=10, delay=3)
    def _get_snapshots_after_trigger(self, snapshots_before):
        step("Get new snapshot after triggering")
        snapshots_after = PlatformSnapshot.api_get_snapshots()
        assert len(snapshots_after) > len(snapshots_before)
        return snapshots_after

    @priority.medium
    def test_trigger_snapshot(self):
        step("Get snapshots")
        snapshots_before = PlatformSnapshot.api_get_snapshots()
        step("Trigger new snapshot")
        PlatformSnapshot.api_trigger_snapshots()
        step("Get snapshots after triggering")
        snapshots_after = self._get_snapshots_after_trigger(snapshots_before)
        step("Get version")
        version = PlatformSnapshot.api_get_version()
        step("Compare snapshot and version")
        assert snapshots_after[0] == version
