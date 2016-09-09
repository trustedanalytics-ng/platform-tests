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
import modules.http_calls.platform.template_repository as template_repository
from fixtures.k8s_templates import template_example


@functools.total_ordering
class Template(object):
    def __init__(self, template_id: str, components: dict, hooks: dict):
        self.id = template_id
        self.components = components
        self.hooks = hooks

    def __eq__(self, other):
        return self.id == other.id and self.components == other.components and self.hooks == other.hooks

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def create(cls, context, template_id=None, body=None, hooks=None):
        if template_id is None:
            template_id = str(uuid.uuid4())
        if body is None:
            body = template_example.ng_template_example_body
        template_repository.create_template(template_id=template_id, template_body=body, hooks=hooks)
        # POST returns empty body
        new_template = cls.get(template_id=template_id)
        context.templates.append(new_template)
        return new_template

    @classmethod
    def get(cls, template_id: str):
        response = template_repository.get_template(template_id)
        return cls._from_response(response)

    @classmethod
    def get_parsed(cls, template_id: str, service_id: str, optional_params={}):
        params = {"serviceId": service_id }
        params.update(optional_params)
        response = template_repository.get_parsed_template(template_id, params)
        return cls._from_response(response)

    @classmethod
    def get_list(cls):
        response = template_repository.get_templates()
        templates = []
        for item in response:
            template = cls._from_response(item)
            templates.append(template)
        return templates

    def delete(self):
        template_repository.delete_template(self.id)

    def cleanup(self):
        self.delete()

    @classmethod
    def _from_response(cls, response):
        return cls(template_id=response["id"], components=response["body"], hooks=response["hooks"])
