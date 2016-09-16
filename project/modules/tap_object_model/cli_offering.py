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

import json

from fixtures.k8s_templates import template_example
from modules.file_utils import save_text_file
from modules.tap_object_model import ServicePlan
from modules.test_names import generate_test_object_name


class CliOffering:
    def __init__(self, name, service_plans, tap_cli):
        self.name = name
        self.service_plans = service_plans
        self.tap_cli = tap_cli

    @staticmethod
    def _create_offering_template(template_body: dict, service_name: str, description: str, bindable: bool,
                                  tags: list, plans: list):
        return {
            "template": {
                "body": template_body,
                "hooks": None
            },
            "services": [{
                "name": service_name,
                "description": description,
                "bindable": bindable,
                "tags": tags,
                "plans": plans,
                "metadata": []
            }]
        }

    @classmethod
    def create(cls, context, tap_cli, label: str=None, service_plans: list=None,
               template_body=template_example.etcd_template["body"]):
        if label is None:
            label = generate_test_object_name(short=True, separator="")
        if service_plans is None:
            service_plans = [ServicePlan(guid=None, name="test", description="test")]
        assert all([isinstance(sp, ServicePlan) for sp in service_plans])
        offering_template = cls._create_offering_template(
            template_body=template_body,
            service_name=label,
            description="Test offering",
            bindable=True,
            tags=["test"],
            plans=[sp.to_dict() for sp in service_plans])

        file_path = save_text_file(file_name=label, data=json.dumps(offering_template))
        tap_cli.create_offering([file_path])
        new_offering = cls(name=label, service_plans=service_plans, tap_cli=tap_cli)
        context.cli_offerings.append(new_offering)
        return new_offering

    def delete(self):
        self.tap_cli.delete_offering([self.name])

    def cleanup(self):
        self.delete()
