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

import modules.http_calls.platform.catalog as catalog_api
from ._catalog_instance_superclass import CatalogInstanceSuperClass


class CatalogInstance(CatalogInstanceSuperClass):

    @classmethod
    def get_all(cls):
        response = catalog_api.get_instances()
        return cls._list_from_response(response)

    @classmethod
    def get(cls, *, instance_id):
        response = catalog_api.get_instance(instance_id=instance_id)
        return cls._from_response(response)

    def update(self, *, field_name, value, prev_value=None, username=None):
        catalog_api.update_instance(instance_id=self.id, field_name=field_name, value=value, prev_value=prev_value,
                                    username=username)
        if field_name == "classId":
            field_name = "class_id"
        setattr(self, field_name, value)

    def delete(self):
        catalog_api.delete_instance(instance_id=self.id)
