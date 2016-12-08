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


class CatalogApplicationInstance(CatalogInstanceSuperClass):
    TYPE = "APPLICATION"

    @classmethod
    def create(cls, context, *, application_id, name=None, instance_type=TYPE, state=TapEntityState.REQUESTED):
        if name is None:
            name = generate_test_object_name().replace("_", "-")
        response = catalog_api.create_application_instance(application_id=application_id, name=name,
                                                           instance_type=instance_type, state=state)
        new_instance = cls._from_response(response)
        context.test_objects.append(new_instance)
        return new_instance

    @classmethod
    def get_all(cls):
        response = catalog_api.get_all_application_instances()
        return cls._list_from_response(response)

    @classmethod
    def get_list_for_application(cls, *, application_id):
        response = catalog_api.get_application_instances(application_id=application_id)
        return cls._list_from_response(response)

    @classmethod
    def get(cls, *, application_id, instance_id):
        response = catalog_api.get_application_instance(application_id=application_id, instance_id=instance_id)
        return cls._from_response(response)

    def update(self, *, field_name, value, prev_value=None, username=None):
        catalog_api.update_application_instance(application_id=self.class_id, instance_id=self.id,
                                                field_name=field_name, value=value, prev_value=prev_value,
                                                username=username)
        if field_name == "classId":
            field_name = "class_id"
        setattr(self, field_name, value)

    def delete(self):
        catalog_api.delete_application_instance(application_id=self.class_id, instance_id=self.id)
