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

import functools
import uuid

import modules.http_calls.platform.image_factory as image_factory
from modules.constants import HttpStatus


@functools.total_ordering
class Image(object):

    def __init__(self, image_id: str):
        self.id = image_id

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, image_id=None):
        if image_id is None:
            image_id = str(uuid.uuid4())
        image_factory.create_image(image_id)
        new_image = cls(image_id)
        context.image_factory.append(new_image)
        return new_image

    def delete(self):
        image_factory.delete_image(image_id=self.id)

    def cleanup(self):
        self.delete()
