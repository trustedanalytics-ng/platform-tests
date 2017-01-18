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
import modules.http_calls.platform.model_catalog as model_catalog_api


class TestModelAdd:

    ARTIFACT_METADATA = {
        "filename": "example_artifact.txt",
        "actions": [ModelArtifact.ARTIFACT_ACTIONS["publish_jar_scoring_engine"]]
    }

    @pytest.fixture(scope="class")
    def actions(self):
        return {
            "publish_jar_scoring_engine": [ModelArtifact.ARTIFACT_ACTIONS["publish_jar_scoring_engine"]],
            "publish_tap_scoring_engine": [ModelArtifact.ARTIFACT_ACTIONS["publish_tap_scoring_engine"]]
        }

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_add_new_model_to_organization(self, context, test_user_clients, role, core_org):
        """
        <b>Description:</b>
        Add new model to model catalog.

        <b>Input data:</b>
        1. User
        2. User role (user or admin)
        3. Organization
        4. Model

        <b>Expected results:</b>
        Test passes when created model exists on models list.

        <b>Steps:</b>
        1. Add model to organization.
        2. Verify that created model is shown on models list.
        """
        client = test_user_clients[role]
        step("Add model to organization using {}".format(role))
        new_model = ScoringEngineModel.create(context, org_guid=core_org, client=client, **MODEL_METADATA)
        step("Check that the model is on model list")
        models = ScoringEngineModel.get_list(org_guid=core_org)
        assert new_model in models

    @priority.high
    def test_cannot_add_new_model_to_organization_with_empty_name(self, context, core_org):
        """
        <b>Description:</b>
        Try to add model with empty name.

        <b>Input data:</b>
        1. Organization
        2. Model with empty name

        <b>Expected results:</b>
        Test passes when model catalog returns a 400 http status.

        <b>Steps:</b>
        1. Prepare metadata with name contains only spaces.
        2. Try to add new model with prepared metadata.
        """
        step("Add model to organization")
        metadata = MODEL_METADATA.copy()
        metadata["name"] = "    "
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST, ScoringEngineModel.create,
                                     context, org_guid=core_org, **metadata)

    @priority.medium
    def test_cannot_add_model_with_auto_generated_metadata(self, context, core_org):
        """
        <b>Description:</b>
        Try to add model with auto generated metadata.

        <b>Input data:</b>
        1. Organization
        2. Model with auto generated metadata

        <b>Expected results:</b>
        Test passes when added model has auto generated metadata - different than those entered during creation.

        <b>Steps:</b>
        1. Prepare metadata with auto generated values.
        2. Try to add new model with prepared metadata.
        3. Verify that added model contains expected metadata.
        """
        step("Try to create model with auto-generated metadata")
        metadata_auto_generated = {
            "added_by": 'test-user',
            "added_on": '2000-01-01 00:00 GMT',
            "modified_by": 'test-user',
            "modified_on": '2000-01-01 00:00 GMT'
        }
        metadata = MODEL_METADATA.copy()
        metadata.update(metadata_auto_generated)
        test_model = ScoringEngineModel.create(context, org_guid=core_org, **metadata)
        step("Check that params for auto-generated metadata do not affect created model")
        incorrect_metadata = []
        for k, v in metadata_auto_generated.items():
            if getattr(test_model, k) == v:
                incorrect_metadata.append("{}={}".format(k, v))
        assert len(incorrect_metadata) == 0, "Incorrect metadata: {}".format(", ".join(incorrect_metadata))
        models = ScoringEngineModel.get_list(org_guid=core_org)
        assert test_model in models

    @priority.medium
    @pytest.mark.parametrize("missing_param", ("name", "creation_tool"))
    def test_cannot_add_model_without_a_required_parameter(self, missing_param, core_org):
        """
        <b>Description:</b>
        Try to add model without required parameter.

        <b>Input data:</b>
        1. Model with missing parameter: name or creation tool.
        2. Organization

        <b>Expected results:</b>
        Test passes when model catalog returns a 400 http status.

        <b>Steps:</b>
        1. Prepare metadata without required parameter.
        2. Try to add new model with prepared metadata.
        """
        step("Check that adding a model without a required parameter ({}) causes an error".format(missing_param))
        metadata = MODEL_METADATA.copy()
        del metadata[missing_param]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     model_catalog_api.insert_model, org_guid=core_org,
                                     **metadata)

    @priority.low
    def test_add_model_with_minimum_required_params(self, context, core_org):
        """
        <b>Description:</b>
        Add new model to model catalog without all params - only required.

        <b>Input data:</b>
        1. Organization
        2. Model with minimum required parameters: creation tool and name

        <b>Expected results:</b>
        Test passes when model is added to model catalog successfully.

        <b>Steps:</b>
        1. Prepare metadata contains only name and creation tool values which are required.
        2. Add model with prepared metadata to model catalog.
        3. Verify that created model is shown on models list.
        """
        step("Add model to organization")
        metadata = {
            "name": MODEL_METADATA["name"],
            "creation_tool": MODEL_METADATA["creation_tool"]
        }
        new_model = ScoringEngineModel.create(context, org_guid=core_org, **metadata)
        models = ScoringEngineModel.get_list(org_guid=core_org)
        assert new_model in models

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_add_new_artifact_to_model(self, sample_model, test_user_clients, role):
        """
        <b>Description:</b>
        Add artifact file to the model.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.
        2. User
        3. User role (user or admin)

        <b>Expected results:</b>
        Test passes when artifact is added to the model successfully.

        <b>Steps:</b>
        1. Add artifact to the model.
        2. Verify that added artifact is shown on model's artifacts list.
        """
        client = test_user_clients[role]
        step("Add new artifact to model using {}".format(role))
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, client=client,
                                                     **self.ARTIFACT_METADATA)
        step("Get artifact {} metadata of model {}".format(new_artifact.id, sample_model.id))
        artifact = ModelArtifact.get_artifact(model_id=sample_model.id, artifact_id=new_artifact.id)
        model_artifacts = ScoringEngineModel.get(model_id=sample_model.id).artifacts
        assert artifact in model_artifacts

    @priority.low
    @pytest.mark.parametrize("artifact_actions_key", ("publish_jar_scoring_engine", "publish_tap_scoring_engine"))
    def test_add_new_artifact_to_model_different_actions(self, sample_model, artifact_actions_key, actions):
        """
        <b>Description:</b>
        Add artifact file with action to the model.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.
        2. Artifact action to verifying.
        3. Available options of artifact action.


        <b>Expected results:</b>
        Test passes when artifact is added to the model with properly action.

        <b>Steps:</b>
        1. Prepare artifact metadata with tested action value.
        2. Add artifact with prepared metadata to the model.
        2. Verify that added artifact has expected actions in metadata.
        """
        action = actions[artifact_actions_key]
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        artifact_metadata["actions"] = action
        step("Add new artifact to model with action {}".format(artifact_actions_key))
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **artifact_metadata)
        new_artifact_actions = new_artifact.actions
        assert new_artifact_actions == artifact_metadata["actions"]

    @priority.medium
    def test_cannot_add_new_artifact_without_artifact_file_field(self, sample_model):
        """
        <b>Description:</b>
        Try to add artifact to the model without required filename parameter.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when model catalog returns a 400 http status.

        <b>Steps:</b>
        1. Prepare artifact metadata without filename parameter.
        2. Try to add artifact with prepared metadata to the model.
        """
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        del artifact_metadata["filename"]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ModelArtifact.upload_artifact, model_id=sample_model.id, **artifact_metadata)

    @priority.low
    def test_add_new_artifact_without_actions_filed(self, sample_model):
        """
        <b>Description:</b>
        Add artifact file without action to the model.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when artifact is added to the model successfully and artifact's actions list is empty.

        <b>Steps:</b>
        1. Prepare artifact metadata without action parameter.
        2. Add artifact with prepared metadata to the model.
        3. Verify that added artifact has an empty list of actions in metadata.
        """
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        del artifact_metadata["actions"]
        step("Add new artifact to model")
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **artifact_metadata)
        artifact_actions = new_artifact.actions
        expected_actions = []
        assert artifact_actions == expected_actions

    @priority.low
    def test_cannot_add_new_artifact_to_non_existing_model(self):
        """
        <b>Description:</b>
        Try to add artifact to the non existing model.

        <b>Input data:</b>
        1. Non existing model guid

        <b>Expected results:</b>
        Test passes when model catalog returns a 404 http status.

        <b>Steps:</b>
        1. Prepare non existing guid of model.
        2. Try to add artifact with prepared metadata to the model with non existing guid.
        """
        non_existing_model = Guid.NON_EXISTING_GUID
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ModelArtifact.upload_artifact, model_id=non_existing_model,
                                     **self.ARTIFACT_METADATA)

    @priority.medium
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_artifact_file_has_been_properly_added(self, sample_model, test_user_clients, role):
        """
        <b>Description:</b>
        Added artifact file has been added properly to the model.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.
        2. User
        3. User role (user or admin)

        <b>Expected results:</b>
        Test passes when added artifact is the same as inserted one.

        <b>Steps:</b>
        1. Add artifact to the model.
        2. Get added artifact from model.
        3. Verify that content of downloaded artifact is correct.
        """
        client = test_user_clients[role]
        step("Add new artifact to model using {}".format(role))
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, client=client, **self.ARTIFACT_METADATA)
        added_file_content = ModelArtifact.get_artifact_file(model_id=sample_model.id, artifact_id=new_artifact.id)
        with open("fixtures/{}".format(self.ARTIFACT_METADATA["filename"]), 'r') as text:
            expected_content = text.read()
        assert added_file_content == expected_content

    @priority.low
    def test_cannot_add_artifact_with_invalid_action(self, sample_model):
        """
        <b>Description:</b>
        Try to add artifact with invalid action.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when model catalog returns a 400 http status.

        <b>Steps:</b>
        1. Prepare artifact metadata with invalid action.
        2. Try to add artifact with prepared metadata to the model.
        """
        step("Try to add artifact with invalid action")
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        artifact_metadata["actions"] = ["invalid-action"]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ModelArtifact.upload_artifact, model_id=sample_model.id,
                                     **artifact_metadata)

    @priority.low
    def test_can_add_artifact_with_two_actions(self, sample_model):
        """
        <b>Description:</b>
        Added artifact file with two actions to the model.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when added artifact has two actions.

        <b>Steps:</b>
         1. Prepare artifact metadata with two actions.
         2. Add artifact with prepared metadata to the model.
         3. Verify that added artifact has expected actions in metadata.
        """
        step("Try to add artifact with two actions")
        artifact_metadata = self.ARTIFACT_METADATA.copy()
        artifact_metadata["actions"].append(ModelArtifact.ARTIFACT_ACTIONS["publish_tap_scoring_engine"])
        new_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **artifact_metadata)
        assert sorted(new_artifact.actions) == sorted(artifact_metadata["actions"])

    @priority.low
    def test_can_add_more_than_one_artifacts_to_model(self, sample_model):
        """
        <b>Description:</b>
        Add two artifacts to the one model.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when first and second artifacts are added to the model successfully.

        <b>Steps:</b>
        1. Add first artifact to the model.
        2. Add second artifact to the model.
        3. Verify that both artifacts are shown on model's artifacts list.
        """
        step("Add new artifact to model")
        uploaded_first_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **self.ARTIFACT_METADATA)
        first_artifact = ModelArtifact.get_artifact(model_id=sample_model.id, artifact_id=uploaded_first_artifact.id)
        step("Try to add second artifact to model")
        uploaded_second_artifact = ModelArtifact.upload_artifact(model_id=sample_model.id, **self.ARTIFACT_METADATA)
        second_artifact = ModelArtifact.get_artifact(model_id=sample_model.id, artifact_id=uploaded_second_artifact.id)
        assert first_artifact in ScoringEngineModel.get(model_id=sample_model.id).artifacts
        assert second_artifact in ScoringEngineModel.get(model_id=sample_model.id).artifacts



