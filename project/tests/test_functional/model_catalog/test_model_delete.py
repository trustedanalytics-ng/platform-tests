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
import modules.http_calls.platform.model_catalog as model_catalog_api
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from modules.tap_object_model.model_artifact import ModelArtifact
from tests.fixtures.assertions import assert_raises_http_exception


class TestModelDelete:

    ARTIFACT_METADATA = {
        "filename": "example_artifact.txt",
        "actions": [ModelArtifact.ARTIFACT_ACTIONS["publish_jar_scoring_engine"]]
    }

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_delete_model(self, sample_model, test_user_clients, role, core_org):
        """
        <b>Description:</b>
        Delete model from model catalog.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.
        2. User
        3. User role (user or role)
        4. Organization

        <b>Expected results:</b>
        Test passes when model is deleted from model catalog successfully.

        <b>Steps:</b>
        1. Delete model from model catalog.
        2. Get list of models from model catalog.
        3. Verify that model does not exist on models list.
        """
        step("Delete model organization using {}".format(role))
        client = test_user_clients[role]
        sample_model.delete(client=client)
        step("Check that the deleted model is not on the list of models")
        models = ScoringEngineModel.get_list(org_guid=core_org)
        assert sample_model not in models

    @priority.low
    def test_cannot_delete_model_twice(self, sample_model):
        """
        <b>Description:</b>
        Try to delete model twice from model catalog.

        <b>Input data:</b>
        1. Example model existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when model catalog returns a 404 http status.

        <b>Steps:</b>
        1. Delete model from model catalog.
        2. Try to delete the same model again.
        """
        step("Delete sample model")
        sample_model.delete()
        step("Try to delete the same model from organization for the second time")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     sample_model.delete, force=True)

    @priority.low
    def test_cannot_delete_non_existing_model(self):
        """
        <b>Description:</b>
        Try to delete non existing model.

        <b>Input data:</b>
        1. Non existing model guid

        <b>Expected results:</b>
        Test passes when model catalog returns a 404 http status.

        <b>Steps:</b>
        1. Try to delete model with non existing guid.
        """
        step("Check that an attempt to delete model which does not exist returns an error")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     model_catalog_api.delete_model, model_id=Guid.NON_EXISTING_GUID)

    @priority.low
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_delete_artifact_and_file(self, model_with_artifact, test_user_clients, role):
        """
        <b>Description:</b>
        Delete artifact file from model.

        <b>Input data:</b>
        1. Example model with artifact existing on models list in model catalog.
        2. User
        3. User role (user or role)

        <b>Expected results:</b>
        Test passes when artifact file and metadata are deleted from model successfully.

        <b>Steps:</b>
        1. Get artifact id.
        2. Delete artifact file from model.
        3. Try to get artifact file.
        4. Try to get artifact metadata.
        """
        client = test_user_clients[role]
        artifact_id = model_with_artifact.artifacts[0].get("id")
        step("Delete artifact {} of model {} using {}".format(artifact_id, model_with_artifact.id, client))
        ModelArtifact.delete_artifact(model_id=model_with_artifact.id, artifact_id=artifact_id,
                                      client=client)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     model_catalog_api.get_model_artifact_file, model_id=model_with_artifact.id,
                                     artifact_id=artifact_id)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     model_catalog_api.get_model_artifact_metadata, model_id=model_with_artifact.id,
                                     artifact_id=artifact_id)

    @priority.low
    def test_cannot_delete_artifact_twice(self, model_with_artifact):
        """
        <b>Description:</b>
        Try to delete artifact twice from model.

        <b>Input data:</b>
        1. Example model with artifact existing on models list in model catalog.

        <b>Expected results:</b>
        Test passes when model catalog returns a 404 http status.

        <b>Steps:</b>
        1. Get artifact id.
        2. Delete artifact from model.
        3. Try to delete the same artifact again.
        """
        artifact_id = model_with_artifact.artifacts[0].get("id")
        step("Delete artifact {} of model {}".format(artifact_id, model_with_artifact.id))
        ModelArtifact.delete_artifact(model_id=model_with_artifact.id, artifact_id=artifact_id)
        step("Try to delete the same artifact from model for the second time")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ModelArtifact.delete_artifact, model_id=model_with_artifact.id,
                                     artifact_id=artifact_id)
