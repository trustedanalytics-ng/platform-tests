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
from modules.tap_object_model.model_artifact import ModelArtifact
from modules.constants import Guid, HttpStatus
from tests.fixtures.assertions import assert_raises_http_exception


class TestModelGet:

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_get_org_models(self, test_user_clients, role, core_org):
        """
        <b>Description:</b>
        Get list of models in org from model catalog using user client with user/admin role.

        <b>Input data:</b>
        1. User
        2. User role (user or admin)
        3. Organization

        <b>Expected results:</b>
        Test passes when user client get list of models successfully.

        <b>Steps:</b>
        1. Get list of models using tested user client.
        2. Get list of models using default client.
        3. Compare responses from previous steps.
        """
        step("List models in an organization using {}".format(role))
        client = test_user_clients[role]
        models = ScoringEngineModel.get_list(org_guid=core_org, client=client)
        step("List or models in an organization using admin")
        expected_models = ScoringEngineModel.get_list(org_guid=core_org)
        step("Check that the two lists are the same")
        assert sorted(models) == sorted(expected_models)

    @priority.low
    def test_cannot_get_models_without_org(self):
        """
        <b>Description:</b>
        Try to get list of models without required organization guid parameter.

        <b>Input data:</b>
        1. -

        <b>Expected results:</b>
        Test passes when model catalog returns a 400 http status.

        <b>Steps:</b>
        1. Try to get list of models without required organization guid parameter.
        """
        step("Try to list models in non existing organization")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ScoringEngineModel.get_list, org_guid=None)

    @priority.medium
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_get_metadata_of_model(self, sample_model, test_user_clients, role):
        """
        <b>Description:</b>
        Get metadata of model from model catalog using user client with user/admin role.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.
        2. User
        3. User role (user or admin)

        <b>Expected results:</b>
        Test passes when user client get list of models successfully.

        <b>Steps:</b>
        1. Get metadata of model using tested user client.
        2. Verify that metadata has expected values.
        """
        step("Get model using {}".format(role))
        client = test_user_clients[role]
        model = ScoringEngineModel.get(model_id=sample_model.id, client=client)
        assert model == sample_model

    @priority.low
    def test_cannot_get_metadata_of_non_existing_model(self):
        """
        <b>Description:</b>
        Try to get metadata of non existing model.

        <b>Input data:</b>
        1. Non existing model guid

        <b>Expected results:</b>
        Test passes when model catalog returns a 404 http status.

        <b>Steps:</b>
        1. Try to get metadata of model with non existing guid.
        """
        step("Try to get metadata of non existing model")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ScoringEngineModel.get, model_id=Guid.NON_EXISTING_GUID)

    @priority.low
    def test_get_artifact_metadata_using_both_clients(self, model_with_artifact, admin_client, test_org_user_client):
        """
        <b>Description:</b>
        Get artifact metadata of model using user client with user/admin role.

        <b>Input data:</b>
        1. Example model with artifact existing on models list in model catalog.
        2. User with role user
        3. User with role admin

        <b>Expected results:</b>
        Test passes when both user clients can get artifact metadata successfully.

        <b>Steps:</b>
        1. Get artifact metadata using user client.
        2. Get artifact metadata using admin client.
        3. Compare responses from previous steps.
        """
        artifact_id = model_with_artifact.artifacts[0].get("id")
        step("Get artifact {} metadata of model {} using user client".format(artifact_id, model_with_artifact.id))
        artifact_metadata = ModelArtifact.get_artifact(model_id=model_with_artifact.id, artifact_id=artifact_id,
                                                       client=test_org_user_client)
        step("Get artifact {} metadata of model {} using admin client".format(artifact_id, model_with_artifact.id))
        expected_artifact_metadata = ModelArtifact.get_artifact(model_id=model_with_artifact.id,
                                                                artifact_id=artifact_id, client=admin_client)
        assert artifact_metadata == expected_artifact_metadata

    @priority.low
    def test_get_artifact_file_using_both_clients(self, model_with_artifact, admin_client, test_org_user_client):
        """
        <b>Description:</b>
        Get artifact file from model using user client with user/admin role.

        <b>Input data:</b>
        1. Example model with artifact existing on models list in model catalog.
        2. User with role user
        3. User with role admin

        <b>Expected results:</b>
        Test passes when both user clients can get artifact file successfully.

        <b>Steps:</b>
        1. Get artifact file using user client.
        2. Get artifact file using admin client.
        3. Compare responses from previous steps.
        """
        artifact_id = model_with_artifact.artifacts[0].get("id")
        step("Get file of artifact {} using user client".format(artifact_id))
        artifact_file = ModelArtifact.get_artifact_file(model_id=model_with_artifact.id, artifact_id=artifact_id,
                                                        client=test_org_user_client)
        step("Get file of artifact {} using admin client".format(artifact_id))
        expected_content = ModelArtifact.get_artifact_file(model_id=model_with_artifact.id, artifact_id=artifact_id,
                                                           client=admin_client)
        assert artifact_file == expected_content
