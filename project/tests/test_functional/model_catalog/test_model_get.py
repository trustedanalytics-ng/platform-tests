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
        step("List models in an organization using {}".format(role))
        client = test_user_clients[role]
        models = ScoringEngineModel.get_list(org_guid=core_org, client=client)
        step("List or models in an organization using admin")
        expected_models = ScoringEngineModel.get_list(org_guid=core_org)
        step("Check that the two lists are the same")
        assert sorted(models) == sorted(expected_models)

    @priority.low
    def test_cannot_get_models_without_org(self):
        step("Try to list models in non existing organization")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     ScoringEngineModel.get_list, org_guid=None)

    @priority.medium
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_get_metadata_of_model(self, sample_model, test_user_clients, role):
        step("Get model using {}".format(role))
        client = test_user_clients[role]
        model = ScoringEngineModel.get(model_id=sample_model.id, client=client)
        assert model == sample_model

    @priority.low
    def test_cannot_get_metadata_of_non_existing_model(self):
        step("Try to get metadata of non existing model")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ScoringEngineModel.get, model_id=Guid.NON_EXISTING_GUID)

    @priority.low
    def test_get_artifact_metadata_using_both_clients(self, model_with_artifact, admin_client, test_org_user_client):
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
        artifact_id = model_with_artifact.artifacts[0].get("id")
        step("Get file of artifact {} using user client".format(artifact_id))
        artifact_file = ModelArtifact.get_artifact_file(model_id=model_with_artifact.id, artifact_id=artifact_id,
                                                        client=test_org_user_client)
        step("Get file of artifact {} using admin client".format(artifact_id))
        expected_content = ModelArtifact.get_artifact_file(model_id=model_with_artifact.id, artifact_id=artifact_id,
                                                           client=admin_client)
        assert artifact_file == expected_content
