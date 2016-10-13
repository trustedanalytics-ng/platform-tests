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

import modules.http_calls.platform.template_repository as template_repository_api
from fixtures.k8s_templates import template_example
from ._tap_object_superclass import TapObjectSuperclass


class Template(TapObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["id", "components", "hooks"]

    def __init__(self, *, template_id: str, components: dict, hooks: dict):
        super().__init__(object_id=template_id)
        self.components = components
        self.hooks = hooks

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, *, template_id=None, body=template_example.example_template_body, hooks=None):
        if template_id is None:
            template_id = str(uuid.uuid4())
        template_repository_api.create_template(template_id=template_id, template_body=body, hooks=hooks)
        # POST returns empty body
        context.templates.append(cls(template_id=template_id, components=body, hooks=hooks))
        new_template = cls.get(template_id=template_id)
        return new_template

    @classmethod
    def get(cls, *, template_id: str):
        response = template_repository_api.get_template(template_id=template_id)
        return cls._from_response(response)

    @classmethod
    def get_parsed(cls, *, template_id: str, instance_id: str, optional_params: dict=None):
        params = {
            "instanceId": instance_id,
        }
        if optional_params is not None:
            params.update(optional_params)
        response = template_repository_api.get_parsed_template(template_id=template_id, params=params)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = template_repository_api.get_templates()
        return cls._list_from_response(response)

    def delete(self):
        template_repository_api.delete_template(template_id=self.id)

    @classmethod
    def _from_response(cls, response):
        return cls(template_id=response["id"], components=response["body"], hooks=response["hooks"])
