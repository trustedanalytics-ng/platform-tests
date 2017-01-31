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

from modules.constants import TapComponent
from ..http_client.http_client_factory import HttpClientFactory
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider


def _get_client():
    configuration = K8sServiceConfigurationProvider.get(TapComponent.auth_gateway, api_endpoint="")
    return HttpClientFactory.get(configuration)

def get_synchronization_state_of_all_orgs():
    """GET /state"""
    return _get_client().request(
        method=HttpMethod.GET,
        path="state",
        msg="Auth-gateway: get synchronization state of all organizations"
    )

def get_org_synchronization_state(org_guid):
    """GET /state/organizations/{org_guid}"""
    return _get_client().request(
        method=HttpMethod.GET,
        path="state/organizations/{org_guid}",
        path_params={'org_guid': org_guid},
        msg="Auth-gateway: get synchronization state of organization"
    )

def get_user_synchronization_state(org_guid, user_id):
    """GET /state/organizations/{org_guid}/users/{user_id}"""
    return _get_client().request(
        method=HttpMethod.GET,
        path="state/organizations/{org_guid}/users/{user_id}",
        path_params={'org_guid': org_guid, 'user_id': user_id},
        msg="Auth-gateway: get synchronization state of user"
    )

def synchronize_orgs_and_users():
    """PUT /synchronize"""
    return _get_client().request(
        method=HttpMethod.PUT,
        path="synchronize",
        msg="Auth-gateway: synchronize organizations and users"
    )

def synchronize_org(org_guid):
    """PUT /synchronize/organizations/{org_guid}"""
    return _get_client().request(
        method=HttpMethod.PUT,
        path="synchronize/organizations/{org_guid}",
        path_params={'org_guid': org_guid},
        msg="Auth-gateway: synchronize organization"
    )

def synchronize_user_in_org(org_guid, user_id):
    """PUT /synchronize/organizations/{org_guid}/users/{user_id}"""
    return _get_client().request(
        method=HttpMethod.PUT,
        path="synchronize/organizations/{org_guid}/users/{user_id}",
        path_params={'org_guid': org_guid, 'user_id': user_id},
        msg="Auth-gateway: synchronize user in organization"
    )