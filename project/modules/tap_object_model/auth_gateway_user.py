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
from ._tap_object_superclass import TapObjectSuperclass


class AuthGatewayUser(TapObjectSuperclass):

    def __init__(self, user_guid, name, is_synchronized: bool):
        super().__init__(object_id=user_guid)
        self.name = name
        self.is_synchronized = is_synchronized

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    @classmethod
    def synchronize_user_in_org(cls, org_guid, user_id):
        response = auth_gateway.synchronize_user_in_org(org_guid=org_guid, user_id=user_id)
        return cls.from_response(response)

    @classmethod
    def get_user_state(cls, org_guid, user_id):
        response = auth_gateway.get_user_synchronization_state(org_guid=org_guid, user_id=user_id)
        return cls.from_response(response)

    @classmethod
    def _from_response(cls, response):
        user = cls(user_guid=response["guid"], name=response["name"], is_synchronized=response["synchronized"])
        return user

    @classmethod
    def from_response(cls, response):
        return cls._from_response(response)

    @classmethod
    def list_from_response(cls, response):
        return cls._list_from_response(response)