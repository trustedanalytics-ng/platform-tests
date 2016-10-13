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

import pytest
from unittest import mock

from modules.tap_object_model import ServiceOffering
from modules.tap_object_model._service_plan import ServicePlan


OFFERING_LABEL = "test_label"
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
    "description": "Test offering",
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

