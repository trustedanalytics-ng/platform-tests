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


def api_get_jobs_list(org_guid, amount, unit, client=None):
    """GET /rest/v1/oozie/jobs/workflow"""
    client = client or PlatformApiClient.get_admin_client()
    params = {
        "amount": amount,
        "org": org_guid,
        "unit": unit
    }
    return client.request("GET", "rest/v1/oozie/jobs/workflow", params=params)


def api_create_job(org_guid, name, start=None, end=None, amount=None, unit=None, zone_id=None, check_column=None,
                   import_mode=None, jdbc_uri=None, last_value=None, password=None, table=None, target_dir=None,
                   username=None, client=None):
    """POST /rest/v1/oozie/schedule_job/coordinated"""
    client = client or PlatformApiClient.get_admin_client()
    params = {"org": org_guid}
    frequency = {"amount": amount, "unit": unit}
    body_schedule_keys = ["start", "end", "frequency", "zoneId"]
    body_schedule_values = [start, end, frequency, zone_id]
    body_schedule = {key: val for key, val in zip(body_schedule_keys, body_schedule_values) if val is not None}
    body_sqoop_keys = ["checkColumn", "importMode", "jdbcUri", "lastValue", "password", "table", "targetDir", "username"]
    body_sqoop_values = [check_column, import_mode, jdbc_uri, last_value, password, table, target_dir, username]
    body_sqoop = {key: val for key, val in zip(body_sqoop_keys, body_sqoop_values) if val is not None}
    body = {"name": name, "schedule": body_schedule, "sqoopImport": body_sqoop}
    return client.request("POST", "rest/v1/oozie/schedule_job/coordinated", params=params, body=body)


def api_get_job_details(org_guid, job_id, client=None):
    """GET /rest/v1/oozie/jobs/workflow/{id}"""
    client = client or PlatformApiClient.get_admin_client()
    params = {"org": org_guid}
    return client.request("GET", "rest/v1/oozie/jobs/workflow/{}".format(job_id), params=params)
