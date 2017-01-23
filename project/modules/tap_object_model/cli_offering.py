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

from retry import retry

from fixtures.k8s_templates import template_example
from modules.file_utils import save_text_file
from modules.test_names import generate_test_object_name
from ._cli_object_superclass import CliObjectSuperclass
from ._service_plan import ServicePlan


class CliOffering(CliObjectSuperclass):
    EXPECTED_CREATE_OFFERING_SUCCESS = 'OK'
    _COMPARABLE_ATTRIBUTES = ["name", "plans"]
    OFFERING_DESC = "Test offering"

    def __init__(self, name, plans, tap_cli):
        super().__init__(tap_cli=tap_cli, name=name)
        self.plans = plans

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
    def create(cls, context, tap_cli, name: str = None, plans: list = None,
               template_body=template_example.etcd_template["body"]):
        if name is None:
            name = generate_test_object_name(short=True, separator="")
        if plans is None:
            plans = [ServicePlan(plan_id=None, name="test", description="test")]
        assert all([isinstance(sp, ServicePlan) for sp in plans])
        offering_template = cls._create_offering_template(
            template_body=template_body,
            service_name=name,
            description=cls.OFFERING_DESC,
            bindable=True,
            tags=["test"],
            plans=[sp.to_dict() for sp in plans])

        file_path = save_text_file(file_name=name, data=json.dumps(offering_template))
        create_output = tap_cli.create_offering(file_path)
        assert cls.EXPECTED_CREATE_OFFERING_SUCCESS in create_output, "Create offering failed: {}".format(create_output)
        new_offering = cls(name=name, plans=plans, tap_cli=tap_cli)
        context.test_objects.append(new_offering)
        return new_offering

    @retry(AssertionError, tries=12, delay=5)
    def ensure_offering_info_succeed(self):
        assert self.OFFERING_DESC in self.tap_cli.print_offering(self.name), "Info for offering '{}' could not be printed".format(self.name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_on_offering_list(self):
        assert self.name in self.tap_cli.list_offerings(), "Offering '{}' is not in the offerings list".format(self.name)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_not_on_offering_list(self):
        assert self.name not in self.tap_cli.list_offerings(), "Offering '{}' is in the offerings list".format(self.name)

    def delete(self):
        self.tap_cli.delete_offering(self.name)
