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

from modules.service_tools.seahorse import Seahorse
from modules.tap_object_model import Organization, Space


class TestSeahorse:
    WORKFLOW_NAME = "Text Message Spam Detection"
    SEAHORSE_ORG_NAME = "seahorse"
    SEAHORSE_SPACE_NAME = "seahorse"

    @pytest.fixture(scope="class")
    def seahorse_org(self):
        # TODO use test_org instead of this fixture when seahorse is fully integrated
        orgs = Organization.api_get_list()
        seahorse_org = next((o for o in orgs if o.name == self.SEAHORSE_ORG_NAME), None)
        assert seahorse_org is not None, "No seahorse org found"
        return seahorse_org

    @pytest.fixture(scope="class")
    def seahorse_space(self):
        # TODO use test_space instead of this fixture when seahorse is fully integrated
        spaces = Space.api_get_list()
        seahorse_space = next((s for s in spaces if s.name == self.SEAHORSE_SPACE_NAME), None)
        assert seahorse_space is not None, "No seahorse space found"
        return seahorse_space

    @pytest.fixture(scope="class")
    def seahorse(self, request, admin_client, seahorse_org, seahorse_space):
        seahorse = Seahorse(seahorse_org.guid, seahorse_space.guid, admin_client)
        request.addfinalizer(seahorse.cleanup)
        return seahorse

    def test_0_there_are_example_workflows(self, seahorse):
        workflows = seahorse.get_workflows()
        assert len(workflows) > 5

    def test_1_workflow_can_be_cloned(self, seahorse):
        some_workflow_id = seahorse.get_workflow_id_by_name(self.WORKFLOW_NAME)
        seahorse.clone_workflow(some_workflow_id)

    def test_2_workflow_can_be_launched(self, seahorse):
        workflow_id_to_be_cloned = seahorse.get_workflow_id_by_name(self.WORKFLOW_NAME)
        cloned_workflow_id = seahorse.clone_workflow(workflow_id_to_be_cloned)
        seahorse.start_editing(cloned_workflow_id)
        seahorse.launch(cloned_workflow_id)
        seahorse.assert_n_nodes_completed_successfully(14)
        seahorse.stop_editing(cloned_workflow_id)

