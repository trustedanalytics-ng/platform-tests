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

from retry import retry

import modules.http_calls.platform.catalog as catalog_api
from ._tap_object_superclass import TapObjectSuperclass


class CatalogImage(TapObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["id", "type", "state", "blob_type"]

    def __init__(self, *, image_id: str, image_type: str, state: str, blob_type: str):
        super().__init__(object_id=image_id)
        self.type = image_type
        self.state = state
        self.blob_type = blob_type

    def __repr__(self):
        return "{} (type={}, id={})".format(self.__class__.__name__, self.type, self.id)

    @classmethod
    def _from_response(cls, response):
        return cls(image_id=response["id"], image_type=response["type"], state=response["state"],
                   blob_type=response["blobType"])

    @classmethod
    def create(cls, context, *, image_type=None, state=None):
        response = catalog_api.create_image(image_type=image_type, state=state)
        new_image = cls._from_response(response)
        context.catalog.append(new_image)
        return new_image

    @classmethod
    def get(cls, *, image_id: str):
        response = catalog_api.get_image(image_id=image_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog_api.get_images()
        return cls._list_from_response(response)

    @retry(AssertionError, tries=10, delay=2)
    def ensure_in_state(self, expected_state):
        image = self.get(image_id=self.id)
        self.state = image.state
        assert self.state == expected_state, "State is {}, expected {}".format(self.state, expected_state)

    def update(self, *, field_name, value):
        setattr(self, field_name, value)
        catalog_api.update_image(image_id=self.id, field_name=field_name, value=value)

    def delete(self):
        catalog_api.delete_image(image_id=self.id)
