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

import uuid

import modules.http_calls.platform.image_factory as image_factory_api
from ._tap_object_superclass import TapObjectSuperclass


class Image(TapObjectSuperclass):
    _COMPARABLE_ATTIBUTES = ["id"]

    def __init__(self, image_id: str):
        super().__init__(object_id=image_id)

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, *, image_id=None):
        if image_id is None:
            image_id = str(uuid.uuid4())
        image_factory_api.create_image(image_id=image_id)
        new_image = cls(image_id)
        context.test_objects.append(new_image)
        return new_image

    def delete(self):
        image_factory_api.delete_image(image_id=self.id)
