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
import requests

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import TapComponent as TAP, ServiceCatalogHttpStatus as HttpStatus, ServiceLabels, Urls
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, long, priority
from modules.tap_object_model import DataSet, ServiceInstance, ServiceKey, Transfer, User
from modules.test_names import get_test_name
from tests.fixtures.test_data import TestData


logged_components = (TAP.scoring_engine, TAP.service_catalog, TAP.application_broker, TAP.das, TAP.hdfs_downloader,
                     TAP.metadata_parser)
pytestmark = [components.scoring_engine, components.service_catalog, components.application_broker]


class TestScoringEngineInstance(TapTestCase):

    SE_PLAN_NAME = "Simple"

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def model_transfer(cls, test_org, test_space, add_admin_to_test_org):
        # TODO change to a session-scoped fixture
        cls.step("Create a transfer and get hdfs path")
        transfer = Transfer.api_create(category="other", org_guid=test_org.guid, source=Urls.model_url)
        transfer.ensure_finished()
        ds = DataSet.api_get_matching_to_transfer(org=test_org, transfer_title=transfer.title)
        cls.hdfs_path = ds.target_uri

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_test_users(cls, test_org, test_space):
        space_manager = User.api_create_by_adding_to_space(org_guid=test_org.guid, space_guid=test_space.guid,
                                                           roles=User.SPACE_ROLES["manager"])
        space_auditor = User.api_create_by_adding_to_space(org_guid=test_org.guid, space_guid=test_space.guid,
                                                           roles=User.SPACE_ROLES["auditor"])
        space_developer = User.api_create_by_adding_to_space(org_guid=test_org.guid, space_guid=test_space.guid,
                                                             roles=User.SPACE_ROLES["developer"])
        cls.authorised_users = [TestData.admin, space_developer]
        cls.unauthorised_users = [space_manager, space_auditor]

    @long
    @priority.high
    @pytest.mark.skip("DPNG-6705")
    def test_create_delete_for_different_users(self):
        for user in self.authorised_users:
            with self.subTest(user=user):
                self._check_create_delete_for_user(user)

    @priority.medium
    def test_users_lacking_privileges_cannot_create_scoring_engine(self):
        self.step("Checking that users with not enough privileges cannot create scoring engine")
        for user in self.unauthorised_users:
            with self.subTest(user=user):
                client = user.login()
                name = get_test_name()
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    self._create_scoring_engine, client, name)

    def _check_create_delete_for_user(self, user):
        client = user.login()
        name = get_test_name()

        self.step("Try to create scoring engine instance")
        instance, application = self._create_scoring_engine(client, name)

        self.step("Try to create scoring engine instance with the same name and the same user")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_CONFLICT,
                                            self._create_scoring_engine, client, name)
        try:
            self._check_request_to_scoring_engine(application)

            self._create_service_key(instance, client)

            self.step("Delete scoring engine instance using space manager account")
            self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                self._delete_scoring_engine, instance,
                                                self.unauthorised_users[0].login())

            instances = ServiceInstance.api_get_list(space_guid=TestData.test_space.guid)
            self.assertIn(instance, instances, "Scoring engine instance was deleted")
        except AssertionError:
            self.step("Delete scoring engine instance and check it does not show on the list")
            self._delete_scoring_engine(instance, client)

    def _create_service_key(self, instance, client):
        self.step("Create a key for the scoring engine instance and check it")
        instance_key = ServiceKey.api_create(instance.guid)
        summary = ServiceInstance.api_get_keys(TestData.test_space.guid)
        self.assertIn(instance_key, summary[instance], "Key not found")

        self.step("Delete service key")
        instance_key.api_delete(client)

    def _create_scoring_engine(self, client, name):
        self.step("Create test service instance")
        instance = ServiceInstance.api_create(
            org_guid=TestData.test_org.guid,
            space_guid=TestData.test_space.guid,
            service_label=ServiceLabels.SCORING_ENGINE,
            service_plan_name=self.SE_PLAN_NAME,
            name=name,
            params={"TAR_ARCHIVE": self.hdfs_path},
            client=client
        )
        application = self._validate_scoring_engine(instance)
        return instance, application

    def _validate_scoring_engine(self, instance):
        instances_list = ServiceInstance.api_get_list(TestData.test_space.guid)

        self.assertIn(instance, instances_list, "Scoring-engine was not created")

        self.step("Check that the instance exists in summary and has no keys")
        summary = ServiceInstance.api_get_keys(TestData.test_space.guid)

        self.assertIn(instance, summary, "Instance not found in summary")
        self.assertEqual(summary[instance], [], "There are keys for the instance")
        validator = ApplicationStackValidator(self, instance)
        validator.validate(expected_bindings=[ServiceLabels.HDFS])
        return validator.application

    def _delete_scoring_engine(self, instance, client):
        instance.api_delete(client)
        instances = ServiceInstance.api_get_list(space_guid=TestData.test_space.guid)
        self.assertNotIn(instance, instances, "Scoring engine instance was not deleted")

    def _check_request_to_scoring_engine(self, application):
        self.step("try to POST data to scoring engine")
        url = "http://" + application.urls[0] + "/v1/score?data=10.0,1.5,200.0"
        res = requests.post(url, data="", headers={"Accept": "text/plain",
                                                   "Content-Types": "text/plain; charset=UTF-8"})
        self.assertEquals(res.text, "List(-1.0)", "Scoring engine response was wrong")
