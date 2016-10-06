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

from modules.constants import TapEntityState
import modules.http_calls.platform.catalog as catalog_api
from modules.test_names import generate_test_object_name
from ._catalog_instance_superclass import CatalogInstanceSuperClass


class CatalogServiceInstance(CatalogInstanceSuperClass):
    TYPE = "SERVICE"

    @classmethod
    def create(cls, context, *, service_id, name=None, instance_type=TYPE, state=TapEntityState.REQUESTED):
        if name is None:
            name = generate_test_object_name().replace("_", "-")
        response = catalog_api.create_service_instance(service_id=service_id, name=name, instance_type=instance_type,
                                                       state=state)
        new_instance = cls._from_response(response)
        context.catalog.append(new_instance)
        return new_instance

    @classmethod
    def get_all(cls):
        response = catalog_api.get_all_service_instances()
        return cls._list_from_response(response)

    @classmethod
    def get_list_for_service(cls, *, service_id):
        response = catalog_api.get_service_instances(service_id=service_id)
        return cls._list_from_response(response)

    @classmethod
    def get(cls, *, service_id, instance_id):
        response = catalog_api.get_service_instance(service_id=service_id, instance_id=instance_id)
        return cls._from_response(response)

    def update(self, *, field_name, value):
        setattr(self, field_name, value)
        catalog_api.update_service_instance(service_id=self.class_id, instance_id=self.id, field_name=field_name,
                                            value=value)

    def delete(self):
        catalog_api.delete_service_instance(service_id=self.class_id, instance_id=self.id)
