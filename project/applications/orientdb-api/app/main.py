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
from datetime import datetime

import flask
import flask_restful

from db_connector import DBConnector

app = flask.Flask(__name__)
api = flask_restful.Api(app)
db_connector = DBConnector()


class DatabasesResource(flask_restful.Resource):
    """API /databases endpoint."""

    def post(self):
        """Create new database. Expected request json: {"database_name": <database_name>}."""
        request_body = json.loads(flask.request.data.decode())
        database_name = request_body["database_name"]
        if not database_name:
            flask_restful.abort(400, message="Missing database name")
        db_connector.db_create(database_name)
        return flask.Response("OK")


class DatabaseResource(flask_restful.Resource):
    """API /databases/<database_name> endpoint."""

    def get(self, database_name):
        """Get database info."""
        clusters = db_connector.db_open(database_name)
        details = [str(c) for c in clusters]
        return flask.make_response(flask.jsonify({'Details': details}), 200)

    def delete(self, database_name):
        """Delete database."""
        db_connector.db_drop(database_name)
        return flask.Response("OK")


class ClassesResource(flask_restful.Resource):
    """API /databases/<database_name>/classes endpoint."""

    def post(self, database_name):
        """Create new class. Expected request json: {"class_name": <class_name>}."""
        request_body = json.loads(flask.request.data.decode())
        class_name = request_body["class_name"]
        if not class_name:
            flask_restful.abort(400, message="Missing class name")
        db_connector.class_create(database_name, class_name)
        return flask.Response("OK")


class ClassResource(flask_restful.Resource):
    """API /databases/<database_name>/classes/<class_name> endpoint."""

    def delete(self, database_name, class_name):
        """Delete class."""
        db_connector.class_drop(database_name, class_name)
        return flask.Response("OK")


class RecordsResource(flask_restful.Resource):
    """API /databases/<database_name>/classes/<class_name>/records endpoint."""

    def get(self, database_name, class_name):
        """Get all records from class."""
        results = db_connector.record_get_all(database_name, class_name)
        records = [str(r) for r in results]
        return flask.make_response(flask.jsonify({'Records': records}), 200)

    def post(self, database_name, class_name):
        """Create new record. Expected request json: {"key": <value>}."""
        request_body = json.loads(flask.request.data.decode())
        values = ["{}='{}'".format(k, v) for k, v in request_body.items()]
        values.extend(["id={}".format(datetime.now().strftime("%s"))])
        db_connector.record_create(database_name, class_name, values)
        return flask.Response("OK")


class RecordResource(flask_restful.Resource):
    """API /databases/<database_name>/classes/<class_name>/records/<record_id> endpoint."""

    def get(self, database_name, class_name, record_id):
        """Get record."""
        results = db_connector.record_get_one(database_name, class_name, record_id)
        records = [str(r) for r in results]
        return flask.make_response(flask.jsonify({'Records': records}), 200)

    def delete(self, database_name, class_name, record_id):
        """Delete record."""
        db_connector.record_drop(database_name, class_name, record_id)
        return flask.Response("OK")


class AppCheckResource(flask_restful.Resource):
    """Endpoint to check if the application responds to requests"""

    def get(self):
        return "OrientDb api example"


api.add_resource(AppCheckResource, "/")
api.add_resource(DatabasesResource, "/rest/databases")
api.add_resource(DatabaseResource, "/rest/databases/<database_name>")
api.add_resource(ClassesResource, "/rest/databases/<database_name>/classes")
api.add_resource(ClassResource, "/rest/databases/<database_name>/classes/<class_name>")
api.add_resource(RecordsResource, "/rest/databases/<database_name>/classes/<class_name>/records")
api.add_resource(RecordResource, "/rest/databases/<database_name>/classes/<class_name>/records/<record_id>")

if __name__ == '__main__':
    app.run()
