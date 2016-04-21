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

import functools

from ..http_calls import platform as api


@functools.total_ordering
class LatestEvent(object):

    COMPARED_ATTRIBUTES = ["category", "id", "message", "source_id", "source_name", "timestamp"]

    def __init__(self, event_id, category, message, source_id, source_name, timestamp, org_id=None):
        self.id = event_id
        self.category = category
        self.message = message
        self.source_id = source_id
        self.source_name = source_name
        self.timestamp = timestamp
        self.org_id = org_id

    def __eq__(self, other):
        return all([getattr(self, a) == getattr(other, a) for a in self.COMPARED_ATTRIBUTES])

    def __lt__(self, other):
        return self.id < other.id

    @classmethod
    def api_get_latest_events(cls, org_guid=None, client=None):
        response = api.api_get_latest_events(org_guid, client)["events"]
        events = []
        for event_data in response:
            event = cls(event_id=event_data["id"], category=event_data["category"], message=event_data["message"],
                        org_id=event_data["organizationId"], source_id=event_data["sourceId"],
                        source_name=event_data["sourceName"], timestamp=event_data["timestamp"])
            events.append(event)
        return events

    @classmethod
    def api_get_latest_events_from_org_metrics(cls, org_guid, client=None):
        response = api.api_get_org_metrics(org_guid, client)["latestEvents"]
        events = []
        for event_data in response:
            event = cls(event_id=event_data["id"], category=event_data["category"], message=event_data["message"],
                        source_id=event_data["sourceId"], source_name=event_data["sourceName"],
                        timestamp=event_data["timestamp"])
            events.append(event)
        return events
