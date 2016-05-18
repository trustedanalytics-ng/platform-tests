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

import flask_restful
import pyorient

from config import Config


class DBConnector(object):
    """OrientDB database connector."""

    def __init__(self):
        self._config = Config()
        self._client = pyorient.OrientDB(self._config.db_hostname, self._config.db_port)
        self._client.connect(self._config.db_username, self._config.db_password)

    def db_exists(self, database_name):
        """Check if given database exists."""
        return self._client.db_exists(database_name, pyorient.STORAGE_TYPE_MEMORY)

    def db_open(self, database_name):
        """Open database connection."""
        if not self.db_exists(database_name):
            flask_restful.abort(404, message="Database '{}' not found".format(database_name))
        return self._client.db_open(
            database_name, self._config.db_username, self._config.db_password, pyorient.DB_TYPE_GRAPH)

    def db_create(self, database_name):
        """Create new database."""
        if self.db_exists(database_name):
            flask_restful.abort(400, message="Database '{}' already exists".format(database_name))
        self._client.db_create(database_name, pyorient.DB_TYPE_GRAPH, pyorient.STORAGE_TYPE_MEMORY)

    def db_drop(self, database_name):
        """Drop database."""
        self.db_open(database_name)
        self._client.db_drop(database_name)

    def class_create(self, database_name, class_name):
        """Create new class."""
        self.db_open(database_name)
        self._client.command("CREATE CLASS {} EXTENDS V".format(class_name))

    def class_drop(self, database_name, class_name):
        """Drop class."""
        self.db_open(database_name)
        try:
            self._client.command("DROP CLASS {}".format(class_name))
        except pyorient.PyOrientCommandException:
            flask_restful.abort(400, message="Cannot drop class '{}' because it contains records".format(class_name))

    def record_get_all(self, database_name, class_name):
        """Get all records"""
        self.db_open(database_name)
        return self._client.query("SELECT * FROM {}".format(class_name))

    def record_get_one(self, database_name, class_name, record_id):
        """Get one record"""
        self.db_open(database_name)
        return self._client.query("SELECT * FROM {} WHERE id='{}'".format(class_name, record_id))

    def record_create(self, database_name, class_name, values):
        """Create new record."""
        self.db_open(database_name)
        self._client.command("INSERT INTO {} SET {}".format(class_name, ", ".join(values)))

    def record_drop(self, database_name, class_name, record_id):
        """Drop record."""
        self.db_open(database_name)
        self._client.command("DELETE VERTEX FROM {} WHERE id='{}'".format(class_name, record_id))
