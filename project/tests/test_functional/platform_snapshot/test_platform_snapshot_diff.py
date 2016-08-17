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
from operator import itemgetter

import pytest
from jsondiff import diff
from retry import retry

from modules.constants import TapComponent as TAP
from modules.http_calls.platform import platform_snapshot
from modules.markers import incremental, priority
from modules.tap_logger import step

logged_components = (TAP.platform_snapshot,)
pytestmark = [pytest.mark.components(TAP.platform_snapshot)]


@incremental
@priority.medium
class TestSnapshotDiff:
    def test_0_create_platform_snapshot_before_changes(self):
        step("Save number of snapshots")
        self.__class__.number_of_snapshots = len(platform_snapshot.api_get_snapshots())
        step("Trigger new platform snapshot before changes in platform")
        platform_snapshot.api_trigger_snapshots()

    @retry(AssertionError, delay=3, tries=10)
    def test_1_ensure_snapshot_was_created(self):
        step("Get platform snapshots before changes")
        snapshots = platform_snapshot.api_get_snapshots()
        self.__class__.number_of_snapshots_after_adding_one = len(snapshots)
        step("Check if snapshot was added")
        assert self.number_of_snapshots_after_adding_one == self.number_of_snapshots + 1, "Snapshot was not created"
        step("Find first snapshot to compare")
        self.__class__.snapshot_0 = next(
            (snapshot for snapshot in snapshots if snapshot["id"] == self.number_of_snapshots_after_adding_one), None)
        assert self.snapshot_0 is not None, "Snapshot was not found"

    def test_2_add_app_to_platform_and_create_snapshot(self, sample_python_app):
        step("Trigger new platform snapshot after adding app to platform")
        platform_snapshot.api_trigger_snapshots()

    @retry(AssertionError, delay=3, tries=10)
    def test_3_ensure_snapshot_was_created_after_changes(self):
        step("Get platform snapshots after changes")
        snapshots = platform_snapshot.api_get_snapshots()
        step("Check if snapshot after changes was added")
        assert len(
            snapshots) == self.number_of_snapshots_after_adding_one + 1, "Snapshot was not created"
        step("Find second snapshot to compare")
        self.__class__.snapshot_1 = next(
            (snapshot for snapshot in snapshots if snapshot["id"] == len(snapshots)), None)
        assert self.snapshot_1 is not None, "Snapshot was not found"

    def test_4_compare_snapshots_diff(self, sample_python_app):
        step("Get platform snapshots diff")
        snapshots = platform_snapshot.api_get_snapshots()
        platform_snapshots_diff = platform_snapshot.api_get_snapshots_diff(snapshot_0_number=len(snapshots) - 1,
                                                                           snapshot_1_number=len(snapshots))
        step("Check platform snapshots diff has all elements")
        assert all(self.element in platform_snapshots_diff for self.element in ["applications", "cdh_services",
                                                                                "cf_services", "created_at_before",
                                                                                "created_at_after"]),\
            "{} element is not present in diff".format(self.element)
        step("Get applications json diff")
        applications_diff = diff(a=sorted(self.snapshot_0["applications"], key=itemgetter("name")),
                                 b=sorted(self.snapshot_1["applications"], key=itemgetter("name")))
        step("Check dates of snapshot diff")
        assert platform_snapshots_diff["created_at_before"] < platform_snapshots_diff[
            "created_at_after"], "Date in 'Before' should be earlier than in 'After'"
        step("Check if pushed application is in platform snapshots applications diff and in json applications diff")
        assert sample_python_app.name in str(
            platform_snapshots_diff["applications"]), "Platform Applications diff is incorrect"
        assert sample_python_app.name in str(applications_diff), "Json diff is incorrect"
