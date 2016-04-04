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

from modules.constants import TapComponent as TAP
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.tap_object_model import LatestEvent


logged_components = (TAP.latest_events_service,)


class LatestEventsService(TapTestCase):
    pytestmark = [components.latest_events_service]

    @priority.low
    def test_latest_events(self):
        self.step("Check that latest events service does not crash after basic request")
        LatestEvent.api_get_latest_events()
