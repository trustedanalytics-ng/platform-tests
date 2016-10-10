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

import json

import pytest

from modules.constants.application_path import ApplicationPath
from modules.tap_logger import step
from modules.markers import priority
from modules.service_tools.orientdb_api import OrientDbApi
from modules.tap_object_model import Application, ServiceInstance, ServiceType
from modules.test_names import generate_test_object_name
from modules.constants import ServiceLabels


@pytest.mark.skip(reason="DPNG-8773 Adjust test_orientdb tests to TAP NG")
class TestOrientDB(object):
    """OrientDB functional tests."""

    _API = None

    @pytest.fixture(scope="class", autouse=True)
    def orientdb_service(self, class_context, test_org, test_space):
        """SetUp: OrientDB service creation."""
        step("Create OrientDB service instance.")
        marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
        orient_db = next((service for service in marketplace if service.label == ServiceLabels.ORIENT_DB), None)
        assert orient_db is not None, "{} service is not available in Marketplace".format(ServiceLabels.ORIENT_DB)
        instance_name = generate_test_object_name()
        return ServiceInstance.api_create(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.ORIENT_DB,
            name=instance_name,
            service_plan_guid=orient_db.service_plan_guids[0]
        )

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def orientdb_app(cls, test_space, login_to_cf, orientdb_service, class_context):
        """SetUp: OrientDB API application creation."""
        step("Push OrientDB Api application to cf.")
        app = Application.push(class_context, space_guid=test_space.guid, source_directory=ApplicationPath.ORIENTDB_API,
                               bound_services=(orientdb_service.name,))
        cls._API = OrientDbApi(app)

    @pytest.fixture(scope="function", autouse=True)
    def cleanup(self, request):
        """TearDown: OrientDB database drop."""
        request.addfinalizer(lambda: self._API.database_delete())

    @priority.high
    def test_create_database(self):
        """Creating database."""
        # when
        self._API.database_create()
        # then
        response = self._API.database_get()
        assert "Details" in response

    @priority.medium
    def test_create_class(self):
        """Creating class."""
        # given
        self._API.database_create()
        # when
        self._API.class_create()
        # then
        response = self._API.record_get_all()
        assert "Records" in response
        assert len(response["Records"]) == 0

    @priority.low
    def test_drop_class(self):
        """Deleting class."""
        # given
        self._API.database_create()
        self._API.class_create()
        # when
        response = self._API.class_delete()
        # then
        assert response.ok

    @priority.medium
    def test_create_record(self):
        """Creating record."""
        # given
        self._API.database_create()
        self._API.class_create()
        # when
        self._API.record_create()
        # then
        record = self._get_record()
        record["id"] = None
        assert record == self._API.record()

    @priority.low
    def test_drop_record(self):
        """Deleting record."""
        # given
        self._API.database_create()
        self._API.class_create()
        self._API.record_create()
        record = self._get_record()
        # when
        self._API.record_delete(record["id"])
        # then
        response = self._API.record_get_all()
        assert len(response["Records"]) == 0

    def _get_record(self):
        """Get record."""
        response = self._API.record_get_all()
        records = json.loads(response["Records"][0].replace("'", '"'))
        return records["@{}".format(self._API.TEST_CLASS)]
