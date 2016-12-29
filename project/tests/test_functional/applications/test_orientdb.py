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

from modules.tap_logger import step, log_fixture
from modules.markers import priority
from modules.service_tools.orientdb_api import OrientDbApi


class TestOrientDB(object):
    """OrientDB functional tests."""

    @classmethod
    @pytest.fixture(scope="class")
    def orientdb_api(cls, app_bound_orientdb):
        return OrientDbApi(app_bound_orientdb)

    @pytest.fixture(scope="function", autouse=True)
    def cleanup(self, request, orientdb_api):
        request.addfinalizer(lambda: orientdb_api.database_delete())

    @priority.high
    def test_create_database(self, orientdb_api):
        """
        <b>Description:</b>
        Checks if a database can be created.

        <b>Input data:</b>
        1. orientdb-api app with bound database

        <b>Expected results:</b>
        A database was created.

        <b>Steps:</b>
        1. Create a database.
        2. Verify a database was created.
        """
        step("Create database")
        orientdb_api.database_create()
        response = orientdb_api.database_get()
        assert "Details" in response

    @priority.medium
    def test_create_class(self, orientdb_api):
        """
        <b>Description:</b>
        Checks if a class can be created.

        <b>Input data:</b>
        1. orientdb-api app with bound database

        <b>Expected results:</b>
        A class was created.

        <b>Steps:</b>
        1. Create a database.
        2. Create a class.
        3. Verify there are no records.
        """
        step("Create database")
        orientdb_api.database_create()
        step("Create class")
        orientdb_api.class_create()
        step("Get records and check there are none")
        response = orientdb_api.record_get_all()
        assert "Records" in response
        assert len(response["Records"]) == 0

    @priority.low
    def test_drop_class(self, orientdb_api):
        """
        <b>Description:</b>
        Checks if a class can be deleted.

        <b>Input data:</b>
        1. orientdb-api app with bound database

        <b>Expected results:</b>
        A class was deleted.

        <b>Steps:</b>
        1. Create a database.
        2. Create a class.
        3. Delete the class.
        4. Verify the deleted response.
        """
        step("Create database")
        orientdb_api.database_create()
        step("Create class")
        orientdb_api.class_create()
        step("Check that it's possible to delete the class")
        response = orientdb_api.class_delete()
        assert response.ok

    @priority.medium
    def test_create_record(self, orientdb_api):
        """
        <b>Description:</b>
        Checks if a record can be created.

        <b>Input data:</b>
        1. orientdb-api app with bound database

        <b>Expected results:</b>
        A record was created.

        <b>Steps:</b>
        1. Create a database.
        2. Create a class.
        3. Create a record.
        4. Verify the record.
        """
        step("Create database")
        orientdb_api.database_create()
        step("Create class")
        orientdb_api.class_create()
        step("Create a record")
        orientdb_api.record_create()
        step("Get the record and check it's correct")
        record = orientdb_api.extract_record_from_all()
        record["id"] = None
        assert record == orientdb_api.record()

    @priority.low
    def test_drop_record(self, orientdb_api):
        """
        <b>Description:</b>
        Checks if a record can be deleted.

        <b>Input data:</b>
        1. orientdb-api app with bound database

        <b>Expected results:</b>
        A record was deleted.

        <b>Steps:</b>
        1. Create a database.
        2. Create a class.
        3. Create a record.
        4. Delete the record.
        5. Verify the record was deleted.
        """
        step("Create database")
        orientdb_api.database_create()
        step("Create class")
        orientdb_api.class_create()
        step("Create a record")
        orientdb_api.record_create()
        record = orientdb_api.extract_record_from_all()
        step("Delete the record")
        orientdb_api.record_delete(record["id"])
        step("Check that the record is gone")
        response = orientdb_api.record_get_all()
        assert len(response["Records"]) == 0
