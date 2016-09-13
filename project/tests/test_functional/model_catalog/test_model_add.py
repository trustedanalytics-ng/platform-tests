#
# Copyright (c) 2016 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from modules.constants import Guid, HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from tests.fixtures.assertions import assert_raises_http_exception


class TestModelAdd:

    TEST_METADATA = {
        "name": "test-model",
        "description": "Test model description",
        "revision": "revision",
        "algorithm": "algorithm",
        "creation_tool": "creation-tool"
    }

    @pytest.fixture(scope="class")
    def clients(self, admin_client, test_org_user_client):
        # TODO change test case to use test_org_admin_client instead of admin_client - when DPNG-10987 is done
        return {
            "admin_client": admin_client,
            "test_org_user_client": test_org_user_client
        }

    @priority.high
    @pytest.mark.parametrize("test_client_key", ("admin_client", "test_org_user_client"))
    def test_add_new_model_to_organization(self, context, clients, test_client_key):
        client = clients[test_client_key]
        step("Add model to organization using {}".format(test_client_key))
        new_model = ScoringEngineModel.create(context, org_guid=Guid.CORE_ORG_GUID, client=client, **self.TEST_METADATA)
        step("Check that the model is on model list")
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        assert new_model in models

    @pytest.mark.skip(reason="Multiple organizations are not implemented for TAP_NG yet")
    @priority.low
    def test_cannot_add_model_to_non_existing_org(self, context):
        non_existing_org = Guid.NON_EXISTING_GUID
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ScoringEngineModel.create, context, org_guid=non_existing_org,
                                     **self.TEST_METADATA)

    @pytest.mark.bugs("DPNG-11756 Internal server error when creating model for incorrect organization")
    @priority.low
    def test_cannot_add_model_to_org_with_incorrect_guid(self, context):
        incorrect_org = "incorrect-org-guid"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ScoringEngineModel.create, context, org_guid=incorrect_org,
                                     **self.TEST_METADATA)

    @priority.medium
    def test_cannot_add_model_with_auto_generated_metadata(self, context):
        step("Try to create model with auto-generated metadata")
        metadata_auto_generated = {
            "added_by": 'test-user',
            "added_on": '2000-01-01 00:00 GMT',
            "modified_by": 'test-user',
            "modified_on": '2000-01-01 00:00 GMT'
        }
        metadata = self.TEST_METADATA.copy()
        metadata.update(metadata_auto_generated)
        test_model = ScoringEngineModel.create(context, org_guid=Guid.CORE_ORG_GUID, **metadata)
        step("Check that params for auto-generated metadata do not affect created model")
        incorrect_metadata = []
        for k, v in metadata_auto_generated.items():
            if getattr(test_model, k) == v:
                incorrect_metadata.append("{}={}".format(k, v))
        assert len(incorrect_metadata) == 0, "Incorrect metadata: {}".format(", ".join(incorrect_metadata))
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        assert test_model in models

    @pytest.mark.bug(reason="Not allow to insert model without name is not implemented yet - DPNG-11673")
    @priority.medium
    @pytest.mark.parametrize("missing_param", ("name", "creation_tool"))
    def test_cannot_add_model_without_a_required_parameter(self, context, missing_param):
        step("Check that adding a model without a required parameter ({}) causes an error".format(missing_param))
        metadata = self.TEST_METADATA.copy()
        del metadata[missing_param]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ScoringEngineModel.create, context, org_guid=Guid.CORE_ORG_GUID,
                                     **metadata)

    @priority.low
    def test_add_model_with_minimum_required_params(self, context):
        step("Add model to organization")
        metadata = {
            "name": self.TEST_METADATA["name"],
            "creation_tool": self.TEST_METADATA["creation_tool"]
        }
        new_model = ScoringEngineModel.create(context, org_guid=Guid.CORE_ORG_GUID, **metadata)
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        assert new_model in models
