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

from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from modules.constants import Guid


class TestModelGet:

    @pytest.fixture(scope="class")
    def clients(self, admin_client, test_org_user_client):
        # TODO change test case to use test_org_admin_client instead of admin_client - when DPNG-10987 is done
        return {
            "admin_client": admin_client,
            "test_org_user_client": test_org_user_client
        }

    @priority.high
    @pytest.mark.parametrize("test_client_key", ("admin_client", "test_org_user_client"))
    def test_get_org_models(self, clients, test_client_key):
        step("List models in an organization using {}".format(test_client_key))
        client = clients[test_client_key]
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID, client=client)
        step("List or models in an organization using admin")
        expected_models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        step("Check that the two lists are the same")
        assert sorted(models) == sorted(expected_models)

    @priority.medium
    @pytest.mark.parametrize("test_client_key", ("admin_client", "test_org_user_client"))
    def test_get_metadata_of_model(self, sample_model, clients, test_client_key):
        step("Get model using {}".format(test_client_key))
        client = clients[test_client_key]
        model = ScoringEngineModel.get(model_id=sample_model.id, client=client)
        assert model == sample_model
