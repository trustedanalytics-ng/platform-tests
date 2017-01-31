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
from ...http_client.http_client_factory import HttpClientFactory
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider


def api_get_jobs_list(org_guid, amount, unit, client=None):
    """GET /v1/oozie/jobs/workflow"""
    params = {
        "amount": amount,
        "org": org_guid,
        "unit": unit
    }
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="v1/oozie/jobs/workflow",
        params=params
    )


def api_create_job(org_guid, name, start=None, end=None, amount=None, unit=None, zone_id=None, check_column=None,
                   import_mode=None, jdbc_uri=None, last_value=None, password=None, table=None, target_dir=None,
                   username=None, client=None):
    """POST /v1/oozie/schedule_job/coordinated"""
    params = {"org": org_guid}
    frequency = {"amount": amount, "unit": unit}
    body_schedule_keys = ["start", "end", "frequency", "zoneId"]
    body_schedule_values = [start, end, frequency, zone_id]
    body_schedule = {key: val for key, val in zip(body_schedule_keys, body_schedule_values) if val is not None}
    body_sqoop_keys = ["checkColumn", "importMode", "jdbcUri", "lastValue", "password", "table", "targetDir",
                       "username"]
    body_sqoop_values = [check_column, import_mode, jdbc_uri, last_value, password, table, target_dir, username]
    body_sqoop = {key: val for key, val in zip(body_sqoop_keys, body_sqoop_values) if val is not None}
    body = {"name": name, "schedule": body_schedule, "sqoopImport": body_sqoop}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="v1/oozie/schedule_job/coordinated",
        params=params,
        body=body
    )


def api_get_job_details(org_guid, job_id, client=None):
    """GET /v1/oozie/jobs/workflow/{id}"""
    params = {"org": org_guid}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="v1/oozie/jobs/workflow/{job_id}",
        path_params={'job_id': job_id},
        params=params
    )
