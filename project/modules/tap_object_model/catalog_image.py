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

import modules.http_calls.platform.catalog as catalog
from retry import retry


@functools.total_ordering
class CatalogImage(object):
    STATE_READY = "READY"

    def __init__(self, image_id: str, image_type: str, state: str):
        self.id = image_id
        self.type = image_type
        self.state = state

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, image_id=None, image_type=None, state=None):
        if image_id is None:
            image_id = str(uuid.uuid4())
        response = catalog.create_image(image_type=image_type, state=state)
        try:
            new_image = cls._from_response(response)
        except:
            # If exception occurred, check whether image is on the list and if so, delete it.
            image = next((i for i in cls.get_list() if i.id == image_id), None)
            if image is not None:
                image.cleanup()
            raise
        context.catalog.append(new_image)
        return new_image

    @classmethod
    def get(cls, image_id: str):
        response = catalog.get_image(image_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog.get_images()
        images = []
        for item in response:
            image = cls._from_response(item)
            images.append(image)
        return images

    @retry(AssertionError, tries=3, delay=2)
    def ensure_ready(self):
        image = self.get(self.id)
        self.state = image.state
        assert self.state == self.STATE_READY

    def delete(self):
        catalog.delete_image(image_id=self.id)

    def cleanup(self):
        self.delete()

    @classmethod
    def _from_response(cls, response):
        return cls(image_id=response["id"], image_type=response["type"], state=response["state"])
