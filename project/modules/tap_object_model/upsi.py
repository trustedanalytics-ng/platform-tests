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

from ..http_calls import cloud_foundry as cf


class Upsi(object):

    def __init__(self, name, guid, space_guid, credentials):
        self.name = name
        self.guid = guid
        self.space_guid = space_guid
        self.credentials = credentials

    def __repr__(self):
        return "{} (name={}, guid={})".format(self.__class__.__name__, self.name, self.guid)

    @classmethod
    def cf_api_create(cls, name, space_guid, credentials):
        response = cf.cf_api_create_user_provided_service_instance(instance_name=name, space_guid=space_guid,
                                                                   credentials=credentials)
        return cls(guid=response["metadata"]["guid"], name=name, space_guid=space_guid, credentials=credentials)

    @classmethod
    def cf_api_get_list(cls):
        upsi_data = cf.cf_api_get_user_provided_service_instances()
        upsi_list = []
        for data in upsi_data:
            upsi = cls(name=data["entity"]["name"],
                       guid=data["metadata"]["guid"],
                       space_guid=data["entity"]["space_guid"],
                       credentials=data["entity"]["credentials"])
            upsi_list.append(upsi)
        return upsi_list
