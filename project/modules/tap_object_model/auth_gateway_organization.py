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

from modules.http_calls import auth_gateway
from .auth_gateway_user import AuthGatewayUser
from ._tap_object_superclass import TapObjectSuperclass


class AuthGatewayOrganization(TapObjectSuperclass):

    def __init__(self, org_guid, name, is_synchronized: bool, users: list):
        super().__init__(object_id=org_guid)
        self.name = name
        self.users = users
        self.is_synchronized = is_synchronized

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    @classmethod
    def get_platform_state(cls) -> list:
        response = auth_gateway.get_synchronization_state_of_all_orgs()
        return cls._list_from_response(response)

    @classmethod
    def get_org_state(cls, org_guid):
        response = auth_gateway.get_org_synchronization_state(org_guid=org_guid)
        return cls._from_response(response)

    @classmethod
    def synchronize_platform(cls):
        response = auth_gateway.synchronize_orgs_and_users()
        return cls._list_from_response(response)

    @classmethod
    def synchronize_org(cls, org_guid):
        response = auth_gateway.synchronize_org(org_guid=org_guid)
        return cls._from_response(response)

    @classmethod
    def _from_response(cls, response):
        users = AuthGatewayUser.list_from_response(response["users"])
        org = cls(org_guid=response["guid"], name=response["name"], is_synchronized=response["state"], users=users)
        return org
