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

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider
from ...http_client.http_client_factory import HttpClientFactory


def api_get_transfers(org_guids=None, query="", filters=(), size=12, time_from=0, client=None):
    """GET /rest/das/requests"""
    query_params = {
        "query": query,
        "filters": list(filters),
        "size": size,
        "from": time_from
    }
    if org_guids is not None:
        query_params["orgs"] = ",".join(org_guids)
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="/rest/das/requests",
        params=query_params,
        msg="PLATFORM: get filtered transfer list"
    )


def api_create_transfer(category=None, is_public=None, org_guid=None, source=None, title=None, client=None):
    """POST /rest/das/requests"""
    body_keys = ["category", "publicRequest", "orgUUID", "source", "title"]
    values = [category, is_public, org_guid, source, title]
    body = {key: val for key, val in zip(body_keys, values) if val is not None}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="/rest/das/requests",
        body=body,
        msg="PLATFORM: create a transfer"
    )


def api_get_transfer(request_id, client=None):
    """GET /rest/das/requests/{request_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="/rest/das/requests/{}".format(request_id),
        msg="PLATFORM: get transfer"
    )


def api_delete_transfer(request_id, client=None):
    """DELETE /rest/das/requests/{request_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="/rest/das/requests/{}".format(request_id),
        msg="PLATFORM: delete transfer"
    )
