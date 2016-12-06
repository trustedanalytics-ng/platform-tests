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

from modules.constants import Guid, ModelCatalogHttpStatus
import modules.http_calls.platform.model_catalog as model_catalog_api
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from tests.fixtures.assertions import assert_raises_http_exception


class TestModelUpdate:

    UPDATED_METADATA = {
        "name": "updated-model",
        "revision": "updated-revision",
        "algorithm": "updated-algorithm",
        "creation_tool": "updated-creationTool",
        "description": "updated-description"
    }

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_update_model(self, sample_model, test_user_clients, role):
        step("Update model using {}".format(role))
        client = test_user_clients[role]
        sample_model.update(client=client, **self.UPDATED_METADATA)
        step("Check that the model is updated")
        model = ScoringEngineModel.get(model_id=sample_model.id)
        assert model == sample_model

    @priority.medium
    def test_update_only_part_of_metadata_fields(self, sample_model):
        metadata = self.UPDATED_METADATA.copy()
        for m in ("revision", "algorithm", "description"):
            del metadata[m]
        sample_model.update(**metadata)
        model = ScoringEngineModel.get(model_id=sample_model.id)
        assert sample_model == model

    @priority.low
    def test_cannot_update_model_with_non_existing_guid(self):
        assert_raises_http_exception(ModelCatalogHttpStatus.CODE_NOT_FOUND, ModelCatalogHttpStatus.MSG_NOT_FOUND,
                                     model_catalog_api.update_model, model_id=Guid.NON_EXISTING_GUID,
                                     **self.UPDATED_METADATA)

    @pytest.mark.bugs("DPNG-11760 Internal server error on updating model")
    @priority.low
    def test_cannot_update_model_with_incorrect_guid(self):
        invalid_guid = "invalid-model-id"
        assert_raises_http_exception(ModelCatalogHttpStatus.CODE_BAD_REQUEST, ModelCatalogHttpStatus.MSG_BAD_REQUEST,
                                     model_catalog_api.update_model, model_id=invalid_guid, **self.UPDATED_METADATA)

    @priority.high
    @pytest.mark.parametrize("role", ["admin", "user"])
    def test_update_model_metadata(self, sample_model, test_user_clients, role):
        step("Update model name and creation_tool")
        client = test_user_clients[role]
        metadata = {
            "name": "updated-model",
            "creation_tool": "updated-tool"
        }
        sample_model.patch(client=client, **metadata)
        step("Get model and check that metadata are updated")
        model = ScoringEngineModel.get(model_id=sample_model.id)
        assert model == sample_model

    @priority.medium
    def test_updating_auto_generated_metadata_has_no_effect(self, sample_model):
        auto_generated_metadata = {
            "added_by": "test-user",
            "added_on": "2000-01-01 00:00 GMT",
            "modified_by": "test-user",
            "modified_on": "2000-01-01 00:00 GMT"
        }
        step("Try to update model with auto-generated metadata")
        sample_model.patch(**auto_generated_metadata)
        step("Check that params for auto-generated metadata do not affect created model")
        model = ScoringEngineModel.get(model_id=sample_model.id)
        incorrect_metadata = []
        for k, v in auto_generated_metadata.items():
            if getattr(model, k) == v:
                incorrect_metadata.append("{}={}".format(k, v))
        assert len(incorrect_metadata) == 0, "Incorrect metadata: {}".format(", ".join(incorrect_metadata))
        assert model == sample_model

    @pytest.mark.parametrize("missing_param", ("name", "creation_tool"))
    @priority.medium
    @pytest.mark.bugs("DPNG-13394 Error while proxying request to service model-catalog")
    def test_cannot_update_metadata_with_empty_name_filed(self, missing_param, sample_model):
        metadata = self.UPDATED_METADATA.copy()
        del metadata[missing_param]
        assert_raises_http_exception(ModelCatalogHttpStatus.CODE_BAD_REQUEST, ModelCatalogHttpStatus.MSG_BAD_REQUEST,
                                     sample_model.patch, **metadata)
