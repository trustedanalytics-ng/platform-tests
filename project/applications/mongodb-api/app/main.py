#!/usr/bin/env python
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

import flask
from werkzeug.exceptions import default_exceptions, InternalServerError
from pymongo import errors
from bson.json_util import dumps

from config import Config, MongoVersion
from db_utils import DatabaseClient


def _handle_http_exception(error):
    default_error_code = InternalServerError.code
    default_error_description = InternalServerError.description
    return flask.jsonify({
        "status_code": getattr(error, "code", default_error_code),
        "message": str(error),
        "description": getattr(error, "description", default_error_description)
    }), getattr(error, "code", default_error_code)


def _get_request_json(request):
    if request.data:
        return request.json
    return {}


def create_app():
    app = flask.Flask(__name__)
    for code, exception in default_exceptions.items():
        app.errorhandler(code)(_handle_http_exception)
    app.errorhandler(Exception)(_handle_http_exception)  # to handle all exceptions in debug mode
    return app


app = create_app()
c = Config()
db = DatabaseClient()

if c.db_type == MongoVersion['30_MULTINODE']:
    db.configure_mongo_cluster()


@app.route("/")
def index():
    return "Mongodb api example\n"


@app.route("/collections", methods=["GET"])
def collections():
    """
    Returns all collections name list
    :return: {"collections": <collections_name_list>}
    """
    return dumps({"collections": db.get_collection_list()})


@app.route("/collections", methods=["POST"])
def create_collection():
    """
    Creates new colection. Expected request json: {"new_collection": <new_collection_name>}
    :return: "OK" message when everything goes well
    """
    name = _get_request_json(flask.request).get("new_collection")
    if name:
        try:
            db.add_collection(name)
            return "OK"
        except errors.CollectionInvalid as e:
            return flask.Response(e.message, status=400)
    return flask.Response("Bad request", status=400)


@app.route("/collections/<collection_name>", methods=["DELETE"])
def delete_collection(collection_name):
    """
    Deletes <collection_name>
    :param collection_name: Name of the collection we want delete
    :return: "OK" message when everything goes well
    """
    db.delete_collection(collection_name)
    return "OK"


@app.route("/collections/<collection_name>/documents", methods=["GET"])
def get_documents(collection_name):
    """
    Retrieve all documents from the <collection_name>.
    :param collection_name: Name of the collection we want to retrieve rows from
    :return: Json with list of rows. {"rows": <rows_list>}
    """
    return dumps({"rows": db.get_documents(collection_name)})


@app.route("/collections/<collection_name>/documents", methods=["POST"])
def add_documents(collection_name):
    """
    Add new document. Expected request json: {"data": {<property>: <value>}}
    :param collection_name: Modified collection
    :return: return id of the inserted document
    """
    data = _get_request_json(flask.request).get("data")
    if data:
        return dumps({"document_id": db.add_document(collection_name, data)})
    return flask.Response("Bad request.", status=400)


@app.route("/collections/<collection_name>/documents/<document_id>", methods=["POST"])
def replace_document(collection_name, document_id):
    """
    Replace document with id. Expected request json: {"new_data": {<property>: <value>}}
    :param collection_name: Name of modified collection
    :param document_id: Id of replaced document
    :return: "OK" message when everything goes well
    """
    request_json = _get_request_json(flask.request)
    new_data = request_json.get("new_data")
    if new_data:
        db.replace_document(collection_name, document_id, new_data)
        return "OK"
    return flask.Response("Bad request.", status=400)


@app.route("/collections/<collection_name>/documents/<document_id>", methods=["DELETE"])
def delete_document(collection_name, document_id):
    """
    Delete rows that meet filter criteria.
    :param collection_name: Name of modified collection
    :param document_id: Id of deleted document
    :return: "OK" message when everything goes well
    """
    db.delete_document(collection_name, document_id)
    return "OK"


if __name__ == "__main__":
    config = Config()
    app.debug = True
    app.run(host=config.app_host, port=config.app_port)
