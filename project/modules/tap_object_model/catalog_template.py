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

from modules.constants import TapEntityState
import modules.http_calls.platform.catalog as catalog_api


@functools.total_ordering
class CatalogTemplate(object):
    _COMPARABLE_ATTRIBUTES = ["id", "state"]

    def __init__(self, *, template_id: str, state: str):
        self.id = template_id
        self.state = state

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def _from_response(cls, response):
        return cls(template_id=response["templateId"], state=response["state"])

    @classmethod
    def create(cls, context, *, state=TapEntityState.READY):
        response = catalog_api.create_template(state=state)
        new_template = cls._from_response(response)
        context.test_objects.append(new_template)
        return new_template

    @classmethod
    def get(cls, *, template_id: str):
        response = catalog_api.get_template(template_id=template_id)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = catalog_api.get_templates()
        templates = []
        for item in response:
            template = cls._from_response(item)
            templates.append(template)
        return templates

    def update(self, *, field_name, value):
        setattr(self, field_name, value)
        catalog_api.update_template(template_id=self.id, field_name=field_name, value=value)

    def delete(self):
        catalog_api.delete_template(template_id=self.id)

    def cleanup(self):
        self.delete()
