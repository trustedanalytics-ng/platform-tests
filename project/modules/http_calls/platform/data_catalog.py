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

import json

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.http_client_factory import HttpClientFactory
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider


def api_get_datasets(org_guid_list=None, query="", filters=(), size=12, time_from=0, only_private=False,
                     only_public=False, client=None):
    """GET /rest/datasets"""
    query_params = {
        "query": json.dumps({"query": query, "filters": list(filters), "size": size, "from": time_from})
    }
    if org_guid_list is not None:
        query_params["orgs"] = ",".join(org_guid_list)
    if only_private:
        query_params["onlyPrivate"] = only_private
    if only_public:
        query_params["onlyPublic"] = only_public
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/datasets",
        params=query_params,
        msg="PLATFORM: get filtered list of data sets"
    )


def api_get_dataset(entry_id, client=None):
    """GET /rest/datasets/{entry_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="rest/datasets/{}".format(entry_id),
        msg="PLATFORM: get data set"
    )


def api_delete_dataset(entry_id, client=None):
    """DELETE /rest/datasets/{entry_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="rest/datasets/{}".format(entry_id),
        msg="PLATFORM: delete data set"
    )


def api_update_dataset(entry_id, creation_time=None, target_uri=None, category=None, format=None,
                       record_count=None, is_public=None, org_guid=None, source_uri=None, size=None, data_sample=None,
                       title=None, client=None):
    """POST /rest/datasets/{entry_id}"""
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="rest/datasets/{}".format(entry_id),
        body=body,
        msg="PLATFORM: update data set"
    )
