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

from modules.api_client import PlatformApiClient


def api_get_latest_events(org_guid=None, client=None):
    """GET /rest/les/events"""
    client = client or PlatformApiClient.get_admin_client()
    params = {}
    if org_guid is not None:
        params = {"org": org_guid}
    return client.request("GET", "rest/les/events", params=params, log_msg="PLATFORM: get latest events")
