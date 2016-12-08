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
from modules.markers import priority
from modules.tap_object_model.scoring_engine_model import ScoringEngineModel
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception


class TestModelAdd:

    TEST_METADATA = {
        "name": generate_test_object_name(),
        "description": "Test model description",
        "revision": "revision",
        "algorithm": "algorithm",
        "creation_tool": "creation-tool"
    }

    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    @priority.low
    def test_cannot_add_model_to_non_existing_org(self, context):
        non_existing_org = Guid.NON_EXISTING_GUID
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                     ScoringEngineModel.create, context, org_guid=non_existing_org,
                                     **self.TEST_METADATA)
