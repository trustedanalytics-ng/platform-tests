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

import pytest

from modules.tap_object_model import Template


@pytest.mark.usefixtures("open_tunnel")
class TestTemplateRepository:

    def test_pass(self):
        Template.get_list()

    @pytest.mark.bugs("DPNG-9607 [tapng-template-repository] POST for /api/v1/templates returns empty body")
    def test_create_and_delete_template(self, context):
        template = Template.create(context)
        templates = Template.get_list()
        assert template in templates

        template.delete()
        templates = Template.get_list()
        assert template not in templates

