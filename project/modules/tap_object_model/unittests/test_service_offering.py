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

import copy
import json

import pytest
from unittest import mock

from modules.constants import ServicePlan as ServicePlanNames
from modules.tap_object_model import ServiceOffering
from modules.tap_object_model._service_plan import ServicePlan
from tests.fixtures.context import Context


JAR_PATH = "jar/path"
MANIFEST_PATH = "manifest/path"
OFFERING_PATH = "offering/path"

OFFERING_LABEL = "test_label"
OFFERING_DESCRIPTION = "test_description"
OFFERING_TAGS = ["test_tags"]
OFFERING_ID = "5a39667d-3309-4dcf-7acd-7ef4aa81e4ce"
PLAN_0_ID = "a40e801c-3f08-46b0-730a-883d8d9e1bad"
PLAN_0_NAME = "test_0"
PLAN_0_DESCRIPTION = "Test plan 0"
PLAN_1_ID = "de641503-89b8-4bff-5a7e-24e1ee7f5081"
PLAN_1_NAME = "test_1"
PLAN_1_DESCRIPTION = "Test plan 1"

PLAN_0_POST = {
    "id": PLAN_0_ID,
    "name": PLAN_0_NAME,
    "description": PLAN_0_DESCRIPTION,
    "cost": "free",
    "auditTrail": {
        "createdOn": 1473999993,
        "createdBy": "admin",
        "lastUpdatedOn": 1473999993,
        "lastUpdateBy": "admin"
    }
}
PLAN_0_GET = {
    "entity": {
        "name": PLAN_0_NAME,
        "free": True,
        "description": PLAN_0_DESCRIPTION,
        "service_guid": "37c2533c-b2cf-4f1d-5628-0ea01a7b80c3",
        "extra": "",
        "unique_id": PLAN_0_ID,
        "public": True,
        "active": True,
        "service_url": "",
        "service": "",
        "service_instances_url": "",
        "metadata": {
            "guid": ""
        }
    },
    "metadata": {
        "guid": PLAN_0_ID
    }
}

PLAN_1_POST = copy.deepcopy(PLAN_0_POST)
PLAN_1_POST["id"] = PLAN_1_ID
PLAN_1_POST["name"] = PLAN_1_NAME
PLAN_1_POST["description"] = PLAN_1_DESCRIPTION

PLAN_1_GET = copy.deepcopy(PLAN_0_GET)
PLAN_1_GET["metadata"]["guid"] = PLAN_1_ID
PLAN_1_GET["entity"]["unique_id"] = PLAN_1_ID
PLAN_1_GET["entity"]["name"] = PLAN_1_NAME
PLAN_1_GET["entity"]["description"] = PLAN_1_DESCRIPTION


POST_RESPONSE_ONE_PLAN = {
    "id": OFFERING_ID,
    "name": OFFERING_LABEL,
    "description": OFFERING_DESCRIPTION,
    "bindable": True,
    "templateId": "1053f1be-ed03-4b07-69de-47834be9f438",
    "state": "READY",
    "plans": [
        PLAN_0_POST
    ],
    "auditTrail": {
        "createdOn": 1473999993,
        "createdBy": "admin",
        "lastUpdatedOn": 1473999993,
        "lastUpdateBy": "admin"
    },
    "metadata": None
}

GET_RESPONSE_ONE_PLAN = {
    "entity": {
        "label": OFFERING_LABEL,
        "state": "READY",
        "provider": "",
        "url": "",
        "description": "Test test test",
        "long_Description": "",
        "version": "",
        "info_url": "",
        "active": True,
        "bindable": True,
        "unique_id": OFFERING_ID,
        "extra": "",
        "tags": None,
        "requires": None,
        "documentation_url": "",
        "service_broker_guid": "",
        "plan_updateable": True,
        "service_plans_url": "",
        "service_plans": [
            PLAN_0_GET
        ]
    },
    "metadata": {
        "guid": OFFERING_ID
    }
}

POST_RESPONSE_TWO_PLANS = copy.deepcopy(POST_RESPONSE_ONE_PLAN)
POST_RESPONSE_TWO_PLANS["plans"].append(PLAN_1_POST)
GET_RESPONSE_TWO_PLANS = copy.deepcopy(GET_RESPONSE_ONE_PLAN)
GET_RESPONSE_TWO_PLANS["entity"]["service_plans"].append(PLAN_1_GET)


class TestServiceOffering:

    mock_api_conf = mock.MagicMock()
    mock_api_service = mock.MagicMock()
    mock_http_client_factory = mock.MagicMock()
    mock_file_utils = mock.MagicMock()
    mock_generate_test_object_name = mock.MagicMock()

    user_admin = {"user": "admin"}

    mock_http_client_factory.get.return_value = user_admin

    @pytest.mark.parametrize("response", (POST_RESPONSE_ONE_PLAN, GET_RESPONSE_ONE_PLAN))
    def test_offering_from_response(self, response):
        offering = ServiceOffering._from_response(response, client=mock.Mock())
        assert offering.label == OFFERING_LABEL
        assert offering.id == OFFERING_ID

    @pytest.mark.parametrize("response", (PLAN_0_GET, PLAN_0_POST))
    def test_service_plan_from_response(self, response):
        service_plan = ServicePlan.from_response(response)
        assert service_plan.id == PLAN_0_ID
        assert service_plan.name == PLAN_0_NAME
        assert service_plan.description == PLAN_0_DESCRIPTION

    @pytest.mark.parametrize("response", (POST_RESPONSE_ONE_PLAN, GET_RESPONSE_ONE_PLAN))
    def test_one_service_plan_in_offering(self, response):
        offering = ServiceOffering._from_response(response, client=mock.Mock())
        assert len(offering.service_plans) == 1
        plan = offering.service_plans[0]
        assert plan.id == PLAN_0_ID
        assert plan.name == PLAN_0_NAME
        assert plan.description == PLAN_0_DESCRIPTION

    @pytest.mark.parametrize("response", (POST_RESPONSE_TWO_PLANS, GET_RESPONSE_TWO_PLANS))
    def test_one_service_plan_in_offering(self, response):
        offering = ServiceOffering._from_response(response, client=mock.Mock())
        assert len(offering.service_plans) == 2
        plan_0 = next(p for p in offering.service_plans if p.id == PLAN_0_ID)
        plan_1 = next(p for p in offering.service_plans if p.id == PLAN_1_ID)
        assert plan_0.id == PLAN_0_ID
        assert plan_0.name == PLAN_0_NAME
        assert plan_0.description == PLAN_0_DESCRIPTION
        assert plan_1.id == PLAN_1_ID
        assert plan_1.name == PLAN_1_NAME
        assert plan_1.description == PLAN_1_DESCRIPTION

    @mock.patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @mock.patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @mock.patch("modules.tap_object_model.service_offering.api", mock_api_service)
    def test_create_from_binary(self):
        context = Context()
        self.mock_api_service.create_offering_from_binary.return_value = POST_RESPONSE_ONE_PLAN
        offering = ServiceOffering.create_from_binary(context, jar_path=JAR_PATH, manifest_path=MANIFEST_PATH,
                                                      offering_path=OFFERING_PATH)
        assert type(offering) == ServiceOffering
        assert offering.label == OFFERING_LABEL
        self.mock_api_service.create_offering_from_binary.assert_called_with(jar_path=JAR_PATH,
                                                                             manifest_path=MANIFEST_PATH,
                                                                             offering_path=OFFERING_PATH,
                                                                             client=offering._client)

    def test_metadata_to_dict(self):
        keys = ["test_key_a", "test_key_b"]
        values = ["test_value_a", "test_value_b"]
        expected_metadata_dict = {
            keys[0]: values[0],
            keys[1]: values[1]
        }
        metadata = [{"key": keys[0], "value": values[0]},
                    {"key": keys[1], "value": values[1]}]
        metadata_dict = ServiceOffering._metadata_to_dict(metadata)
        assert expected_metadata_dict == metadata_dict

    @mock.patch("modules.tap_object_model.service_offering.file_utils", mock_file_utils)
    def test_create_manifest_json_with_custom_name(self):
        custom_name = "test_file_name"
        app_type = "TEST_TYPE"
        manifest_dict = {
            "type": app_type
        }
        self.mock_file_utils.save_text_file.return_value = MANIFEST_PATH
        manifest_json = ServiceOffering.create_manifest_json(app_type=app_type, file_name=custom_name)
        assert manifest_json == MANIFEST_PATH
        self.mock_file_utils.save_text_file.assert_called_with(data=json.dumps(manifest_dict), file_name=custom_name)

    @mock.patch("modules.tap_object_model.service_offering.file_utils", mock_file_utils)
    def test_create_manifest_json_with_default_name(self):
        default_name = "manifest.json"
        app_type = "TEST_TYPE"
        manifest_dict = {
            "type": app_type
        }
        self.mock_file_utils.save_text_file.return_value = MANIFEST_PATH
        manifest_json = ServiceOffering.create_manifest_json(app_type=app_type)
        assert manifest_json == MANIFEST_PATH
        self.mock_file_utils.save_text_file.assert_called_with(data=json.dumps(manifest_dict), file_name=default_name)

    @mock.patch("modules.tap_object_model.service_offering.file_utils", mock_file_utils)
    @mock.patch("modules.tap_object_model.service_offering.generate_test_object_name", mock_generate_test_object_name)
    def test_create_offering_json_with_default_data(self):
        random_name = "test_name"
        file_name = "offering.json"
        default_plan = [{
            "name": ServicePlanNames.FREE,
            "description": ServicePlanNames.FREE,
            "cost": ServicePlanNames.FREE
        }]
        offering_dict = {
            "name": random_name,
            "description": random_name,
            "metadata": [],
            "bindable": True,
            "tags": [],
            "plans": default_plan
        }
        self.mock_generate_test_object_name.return_value = random_name
        self.mock_file_utils.save_text_file.return_value = OFFERING_PATH
        offering_json = ServiceOffering.create_offering_json()
        assert offering_json == OFFERING_PATH
        self.mock_file_utils.save_text_file.assert_called_with(data=json.dumps(offering_dict), file_name=file_name)

    @mock.patch("modules.tap_object_model.service_offering.file_utils", mock_file_utils)
    def test_create_offering_json_witd_custom_data(self):
        custom_name = "test_name"
        file_name = "offering.json"
        metadata = [{"key": "test_key", "value": "test_value"}]
        tags = ["test_tag_a", "test_tag_b"]
        custom_plan = [{
            "name": ServicePlanNames.BARE,
            "description": ServicePlanNames.CLUSTERED,
            "cost": ServicePlanNames.ENCRYPTED
        }]
        offering_dict = {
            "name": custom_name,
            "description": custom_name,
            "metadata": metadata,
            "bindable": False,
            "tags": tags,
            "plans": custom_plan
        }
        self.mock_file_utils.save_text_file.return_value = OFFERING_PATH
        offering_json = ServiceOffering.create_offering_json(name=custom_name, description=custom_name,
                                                             metadata=metadata, bindable=False, tags=tags,
                                                             plans=custom_plan)
        assert offering_json == OFFERING_PATH
        self.mock_file_utils.save_text_file.assert_called_with(data=json.dumps(offering_dict), file_name=file_name)
