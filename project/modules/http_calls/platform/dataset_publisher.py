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


def api_publish_dataset(category, creation_time, data_sample, format, is_public, org_guid, record_count, size,
                        source_uri, target_uri, title, client=None):
    """POST /rest/tables"""
    client = client or PlatformApiClient.get_admin_client()
    body = {"category": category, "creationTime": creation_time, "dataSample": data_sample, "format": format,
            "isPublic": is_public, "orgUUID": org_guid, "recordCount": record_count, "size": size,
            "sourceUri": source_uri, "targetUri": target_uri, "title": title}
    return client.request("POST", "rest/tables", body=body, log_msg="PLATFORM: publish dataset in hive")
