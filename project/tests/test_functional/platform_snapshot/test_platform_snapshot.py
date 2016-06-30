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

from retry import retry

from modules.constants import TapComponent as TAP
from modules.markers import components
from modules.tap_logger import step
from modules.tap_object_model import PlatformSnapshot

logged_components = (TAP.platform_snapshot,)
pytestmark = [components.platform_snapshot]


class TestSnapshot:

    @retry(AssertionError, tries=10, delay=3)
    def _get_new_snapshot(self, snapshots_before):
        step("Get new snapshot after triggering")
        snapshots_after = PlatformSnapshot.api_get_snapshots()
        assert len(snapshots_after) > len(snapshots_before)
        return snapshots_after[0]

    def test_compare_snapshot_and_version(self):
        step("Get snapshots")
        snapshots = PlatformSnapshot.api_get_snapshots()
        step("Get version")
        version = PlatformSnapshot.api_get_version()
        assert snapshots[0] == version

    def test_trigger_snapshot(self):
        step("Get snapshots")
        snapshots_before = PlatformSnapshot.api_get_snapshots()
        step("Get version")
        version_before = PlatformSnapshot.api_get_version()
        step("Trigger new snapshot")
        PlatformSnapshot.api_trigger_snapshots()
        new_snapshot = self._get_new_snapshot(snapshots_before=snapshots_before)
        step("Get new versions")
        version_after = PlatformSnapshot.api_get_version()
        assert version_before != version_after
        assert new_snapshot == version_after
