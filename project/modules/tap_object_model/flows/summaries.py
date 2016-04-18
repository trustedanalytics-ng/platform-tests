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

from ...http_calls import cloud_foundry as cf
from .. import Application, ServiceInstance, Space


def cf_api_get_space_summary(space_guid: str) -> tuple:
    """
    Return a tuple of Application and ServiceInstance lists for a given space.
    """
    response = cf.cf_api_space_summary(space_guid)
    apps = Application.from_cf_api_space_summary_response(response, space_guid)
    service_instances = ServiceInstance.from_cf_api_space_summary_response(response, space_guid)
    return apps, service_instances


def cf_api_get_org_summary(org_guid: str) -> tuple:
    """
    Return aggregated space summary for all spaces in the organization
    """
    spaces = Space.cf_api_get_list_in_org(org_guid)
    org_apps = []
    org_services = []
    for space in spaces:
        apps, services = cf_api_get_space_summary(space.guid)
        org_apps.extend(apps)
        org_services.extend(services)
    return org_apps, org_services