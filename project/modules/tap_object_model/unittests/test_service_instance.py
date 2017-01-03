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
"""Unit tests for ServiceInstance class"""
import copy
from unittest.mock import MagicMock, patch
import uuid
import time

import pytest

from modules.constants import TapEntityState
from modules.tap_object_model.service_instance import ServiceInstance
from tests.fixtures.context import Context
from modules.exceptions import ServiceInstanceCreationFailed


class TestServiceInstance:
    REQUESTED = TapEntityState.REQUESTED
    STARTING = TapEntityState.STARTING
    RUNNING = TapEntityState.RUNNING
    FAILURE = TapEntityState.FAILURE
    STOPPED = TapEntityState.STOPPED

    OFFERING_LABEL = "test_service"
    OFFERING_ID = str(uuid.uuid4())
    SERVICE_NAME = "test"
    SERVICE_PLAN_ID = str(uuid.uuid4())
    SERVICE_PLAN_NAME = "test_plan"
    SERVICE_URL = "www.some-url.com"
    INSTANCE_ID = str(uuid.uuid4())
    BINDINGS = None
    TYPE = "SERVICE"

    METADATA_LIST = [
        {
            "key": "PLAN_ID",
            "value": SERVICE_PLAN_ID
        },
        {
            "key": "urls",
            "value": SERVICE_URL
        }
    ]

    CREATE_SERVICE_RESPONSE_BODY_TEMPLATE = {
        "id": INSTANCE_ID,
        "name": SERVICE_NAME,
        "type": TYPE,
        "offeringId": OFFERING_ID,
        "bindings": BINDINGS,
        "serviceName": OFFERING_LABEL,
        "metadata": METADATA_LIST,
        "state": None,
        "auditTrail": {
            "createdOn": int(time.time()),
            "createdBy": "admin",
            "lastUpdateOn": int(time.time()),
            "lastUpdateBy": "admin"
        }
    }

    CREATE_SERVICE_RESPONSE_BODY_TEMPLATE_CLASS_ID = {
        "id": INSTANCE_ID,
        "name": SERVICE_NAME,
        "type": TYPE,
        "classId": OFFERING_ID,
        "bindings": BINDINGS,
        "serviceName": OFFERING_LABEL,
        "metadata": METADATA_LIST,
        "state": None,
        "auditTrail": {
            "createdOn": int(time.time()),
            "createdBy": "admin",
            "lastUpdateOn": int(time.time()),
            "lastUpdateBy": "admin"
        }
    }

    GET_CATALOG_RESPONSE = \
        [
            {
                'version': '',
                'requires': None,
                'provider': '',
                'state': 'READY',
                'active': True,
                'documentation_url': '',
                'id': OFFERING_ID,
                'bindable': True,
                'description': 'Test offering',
                'extra': '',
                "offeringPlans": [
                    {
                        "name": SERVICE_PLAN_NAME,
                        "id": SERVICE_PLAN_ID
                    }
                ],
                'info_url': '',
                'tags': None,
                'service_broker_guid': '',
                'service_plans_url': '',
                'name': OFFERING_LABEL,
                'plan_updateable': True,
                'url': '',
                'long_Description': ''
            }
        ]

    mock_api_conf = MagicMock()
    mock_api_service = MagicMock()
    mock_http_client_factory = MagicMock()

    user_admin = {"user": "admin"}

    mock_http_client_factory.get.return_value = user_admin

    @classmethod
    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @pytest.fixture(scope="class")
    def service_instance_running(cls):
        tt = ServiceInstance(service_id=cls.INSTANCE_ID, name=cls.SERVICE_NAME, plan_id=cls.SERVICE_PLAN_ID,
                             offering_id=cls.OFFERING_ID, bindings=cls.BINDINGS, state=cls.RUNNING, url=cls.SERVICE_URL)
        return tt

    @classmethod
    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @pytest.fixture(scope="class")
    def service_instance_requested(cls):
        return ServiceInstance(service_id=cls.INSTANCE_ID, name=cls.SERVICE_NAME, plan_id=cls.SERVICE_PLAN_ID,
                               offering_id=cls.OFFERING_ID, bindings=cls.BINDINGS, state=cls.REQUESTED)

    @classmethod
    @pytest.fixture(scope="function", autouse=True)
    def reset_side_effects(cls):
        cls.mock_api_service.create_service_instance.side_effect = None
        cls.mock_api_service.get_service_instances.side_effect = None

    def get_service_with_state(self, state):
        response_body = copy.deepcopy(self.CREATE_SERVICE_RESPONSE_BODY_TEMPLATE)
        response_body["state"] = state
        return response_body

    def get_service_list_with_state(self, state):
        response_body = self.get_service_with_state(state)
        response_body["serviceName"] = self.OFFERING_LABEL
        response_body["planName"] = self.SERVICE_PLAN_NAME
        return [response_body]

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_create(self, service_instance_running):
        """
        Test create command
        """
        context = Context()
        self.mock_api_service.create_service.return_value = self.get_service_with_state(self.RUNNING)
        service_instance = ServiceInstance.create(context, offering_id=self.OFFERING_ID, name=self.SERVICE_NAME,
                                                  plan_id=self.SERVICE_PLAN_ID)
        assert service_instance == service_instance_running

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_create_with_plan_name(self, service_instance_running):
        """
        Test create_with_plan_name command
        """
        context = Context()
        self.mock_api_service.get_offerings.return_value = self.GET_CATALOG_RESPONSE
        self.mock_api_service.create_service_instance.return_value = self.get_service_with_state(self.RUNNING)
        service_instance = ServiceInstance.create_with_name(context, offering_label=self.OFFERING_LABEL,
                                                            name=self.SERVICE_NAME, plan_name=self.SERVICE_PLAN_NAME)
        assert service_instance == service_instance_running

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_ensure_created_success(self, service_instance_requested):
        """
        Test ensure_created method with success
        """
        self.mock_api_service.get_service.side_effect = [self.get_service_with_state(self.REQUESTED),
                                                         self.get_service_with_state(self.STARTING),
                                                         self.get_service_with_state(self.RUNNING)]
        service_instance_requested.ensure_running()
        assert service_instance_requested.state == self.RUNNING

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_ensure_created_failure(self, service_instance_requested):
        """
        Test ensure_created method with failure
        """
        self.mock_api_service.get_service.side_effect = [self.get_service_with_state(self.REQUESTED),
                                                         self.get_service_with_state(self.STARTING),
                                                         self.get_service_with_state(self.FAILURE)]
        with pytest.raises(ServiceInstanceCreationFailed):
            service_instance_requested.ensure_running()
        assert service_instance_requested.state == self.FAILURE

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_cleanup(self, service_instance_requested):
        """
        Test service instance cleanup
        """
        self.mock_api_service.get_service.side_effect = [self.get_service_with_state(self.RUNNING),
                                                         self.get_service_with_state(self.STOPPED)]
        service_instance_requested.cleanup()
        self.mock_api_service.delete_service.assert_called_with(client=service_instance_requested._client,
                                                                service_id=service_instance_requested.id)

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_get_logs(self, service_instance_running):
        """
        Test service instance cleanup
        """
        test_logs = "test logs"
        self.mock_api_service.get_service_logs.return_value = test_logs
        logs = service_instance_running.get_logs()
        self.mock_api_service.get_service_logs.assert_called_with(client=service_instance_running._client,
                                                                  service_id=service_instance_running.id)
        assert logs == test_logs

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    @patch("modules.tap_object_model._api_model_superclass.ConsoleConfigurationProvider", mock_api_conf)
    @patch("modules.tap_object_model.service_instance.api", mock_api_service)
    def test_service_instance_url(self, service_instance_running):
        """
        Test retrieving url from metadata
        """
        context = Context()
        self.mock_api_service.create_service.return_value = self.get_service_with_state(self.RUNNING)
        service_instance = ServiceInstance.create(context, offering_id=self.OFFERING_ID, name=self.SERVICE_NAME,
                                                  plan_id=self.SERVICE_PLAN_ID)
        assert service_instance.url == service_instance_running.url

    def test_service_instance_metadata_to_dict(self):
        """
        Test service instance _metadata_to_dict
        """
        metadata_dict = ServiceInstance._metadata_to_dict(self.METADATA_LIST)
        assert type(metadata_dict) is dict
        for metadata in self.METADATA_LIST:
            assert metadata["key"] in metadata_dict.keys()
            assert metadata["value"] == metadata_dict[metadata["key"]]

    @patch("modules.tap_object_model._api_model_superclass.HttpClientFactory", mock_http_client_factory)
    def test_from_response_class_id(self, service_instance_running):
        """
        Test _from_response command with classId field
        """
        expected_instance = service_instance_running
        response = self.CREATE_SERVICE_RESPONSE_BODY_TEMPLATE_CLASS_ID
        instance = ServiceInstance._from_response(response)
        assert instance.offering_id == expected_instance.offering_id
