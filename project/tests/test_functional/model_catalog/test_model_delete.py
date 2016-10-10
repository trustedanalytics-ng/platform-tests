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


class TestModelDelete:

    @pytest.fixture(scope="class")
    def clients(self, admin_client, test_org_user_client):
        # TODO change test case to use test_org_admin_client instead of admin_client - when DPNG-10987 is done
        return {
            "admin_client": admin_client,
            "test_org_user_client": test_org_user_client
        }

    @priority.high
    @pytest.mark.parametrize("test_client_key", ("admin_client", "test_org_user_client"))
    def test_delete_model(self, sample_model, clients, test_client_key):
        step("Delete model organization using {}".format(test_client_key))
        client = clients[test_client_key]
        sample_model.delete(client=client)
        step("Check that the deleted model is not on the list of models")
        models = ScoringEngineModel.get_list(org_guid=Guid.CORE_ORG_GUID)
        assert sample_model not in models

    @priority.low
    def test_cannot_delete_model_twice(self, sample_model):
        step("Delete sample model")
        sample_model.delete()
        step("Try to delete the same model from organization for the second time")
        assert_raises_http_exception(ModelCatalogHttpStatus.CODE_NOT_FOUND, ModelCatalogHttpStatus.MSG_MODEL_NOT_FOUND,
                                     sample_model.delete)

    @priority.low
    def test_cannot_delete_non_existing_model(self):
        step("Check that an attempt to delete model which does not exist returns an error")
        assert_raises_http_exception(ModelCatalogHttpStatus.CODE_NOT_FOUND, ModelCatalogHttpStatus.MSG_MODEL_NOT_FOUND,
                                     model_catalog_api.delete_model, model_id=Guid.NON_EXISTING_GUID)
