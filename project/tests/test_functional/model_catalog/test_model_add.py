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

from modules.constants import Guid, HttpStatus
from modules.constants.model_metadata import MODEL_METADATA
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.model_artifact import ModelArtifact
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from tests.fixtures.assertions import assert_raises_http_exception


class TestModelAdd:

    ARTIFACT_METADATA = {
        "filename": "example_artifact.txt",
        "actions": [ModelArtifact.ARTIFACT_ACTIONS["publish_to_marketplace"]]
    }

    @pytest.fixture(scope="class")
    def actions(self):
        return {
            "publish_to_marketplace": [ModelArtifact.ARTIFACT_ACTIONS["publish_to_marketplace"]],
            "publish_to_tap_scoring_engine": [ModelArtifact.ARTIFACT_ACTIONS["publish_to_tap_scoring_engine"]]
        }

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_add_new_model_to_organization(self, context, test_user_clients, role):
        client = test_user_clients[role]
        step("Add model to organization using {}".format(role))
        new_model = ScoringEngineModel.create(context, org_guid=Guid.CORE_ORG_GUID, client=client, **MODEL_METADATA)
        step("Check that the model is on model list")
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        assert new_model in models

    @pytest.mark.bugs("DPNG-11756 Internal server error when creating model for incorrect organization")
    @priority.low
    def test_cannot_add_model_to_org_with_incorrect_guid(self, context):
        incorrect_org = "incorrect-org-guid"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ScoringEngineModel.create, context, org_guid=incorrect_org,
                                     **MODEL_METADATA)

    @priority.medium
    def test_cannot_add_model_with_auto_generated_metadata(self, context):
        step("Try to create model with auto-generated metadata")
        metadata_auto_generated = {
            "added_by": 'test-user',
            "added_on": '2000-01-01 00:00 GMT',
            "modified_by": 'test-user',
            "modified_on": '2000-01-01 00:00 GMT'
        }
        metadata = MODEL_METADATA.copy()
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
        metadata = MODEL_METADATA.copy()
        del metadata[missing_param]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ScoringEngineModel.create, context, org_guid=Guid.CORE_ORG_GUID,
                                     **metadata)

    @priority.low
    def test_add_model_with_minimum_required_params(self, context):
        step("Add model to organization")
        metadata = {
            "name": MODEL_METADATA["name"],
            "creation_tool": MODEL_METADATA["creation_tool"]
        }
        new_model = ScoringEngineModel.create(context, org_guid=Guid.CORE_ORG_GUID, **metadata)
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        assert new_model in models

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    def test_add_new_artifact_to_model(self, sample_model, test_user_clients, role):
        client = test_user_clients[role]
        step("Add new artifact to model using {}".format(role))
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, client=client,
                                                     **self.ARTIFACT_METADATA)
        step("Get artifact {} metadata of model {}".format(new_artifact.id, sample_model.id))
        artifact = ModelArtifact.get_artifact(model_id=sample_model.id, artifact_id=new_artifact.id)
        model_artifacts = ScoringEngineModel.get(model_id=sample_model.id).artifacts
        assert artifact in model_artifacts

    @priority.low
    @pytest.mark.parametrize("artifact_actions_key", ("publish_to_marketplace", "publish_to_tap_scoring_engine"))
    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    def test_add_new_artifact_to_model_different_actions(self, sample_model, artifact_actions_key, actions):
        action = actions[artifact_actions_key]
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        artifact_metadata["actions"] = action
        step("Add new artifact to model with action {}".format(artifact_actions_key))
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **artifact_metadata)
        new_artifact_actions = new_artifact.actions
        assert new_artifact_actions == artifact_metadata["actions"]

    @priority.medium
    def test_cannot_add_new_artifact_without_artifact_file_field(self, sample_model):
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        del artifact_metadata["filename"]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ModelArtifact.upload_artifact, model_id=sample_model.id, **artifact_metadata)

    @priority.low
    def test_add_new_artifact_without_actions_filed(self, sample_model):
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        del artifact_metadata["actions"]
        step("Add new artifact to model")
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **artifact_metadata)
        artifact_actions = new_artifact.actions
        expected_actions = []
        assert artifact_actions == expected_actions

    @priority.low
    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    def test_cannot_add_new_artifact_to_non_existing_model(self):
        non_existing_model = Guid.NON_EXISTING_GUID
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ModelArtifact.upload_artifact, model_id=non_existing_model,
                                     **self.ARTIFACT_METADATA)

    @priority.medium
    @pytest.mark.parametrize("role", ["admin", "user"])
    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    def test_artifact_file_has_been_properly_added(self, sample_model, test_user_clients, role):
        client = test_user_clients[role]
        step("Add new artifact to model using {}".format(role))
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, client=client, **self.ARTIFACT_METADATA)
        added_file_content = ModelArtifact.get_artifact_file(model_id=sample_model.id, artifact_id=new_artifact.id)
        with open("fixtures/{}".format(self.ARTIFACT_METADATA["filename"]), 'r') as text:
            expected_content = text.read()
        assert added_file_content == expected_content

    @priority.low
    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    def test_cannot_add_artifact_with_invalid_action(self, sample_model):
        step("Try to add artifact with invalid action")
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        artifact_metadata["actions"] = ["invalid-action"]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ModelArtifact.upload_artifact, model_id=sample_model.id,
                                     **artifact_metadata)

    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    @priority.low
    def test_cannot_add_artifact_with_two_actions(self, sample_model):
        step("Try to add artifact with two actions")
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        artifact_metadata["actions"].append(ModelArtifact.ARTIFACT_ACTIONS["publish_to_tap_scoring_engine"])
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ModelArtifact.upload_artifact, model_id=sample_model.id,
                                     **artifact_metadata)

    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    @priority.low
    def test_cannot_add_more_than_one_artifacts_to_model(self, sample_model):
        step("Add new artifact to model")
        ModelArtifact.upload_artifact(model_id=sample_model.id, **self.ARTIFACT_METADATA)
        step("Try to add second artifact to model")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ModelArtifact.upload_artifact, model_id=sample_model.id,
                                     **self.ARTIFACT_METADATA)



