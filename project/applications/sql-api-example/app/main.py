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
from werkzeug.exceptions import default_exceptions, InternalServerError, NotFound

from config import Config
from db_utils import DatabaseClient
import input_validation


def _handle_http_exception(error):
    default_error_code = InternalServerError.code
    default_error_description = InternalServerError.description
    return flask.jsonify({
        "status_code": getattr(error, "code", default_error_code),
        "message": str(error),
        "description": getattr(error, "description", default_error_description)
    }), getattr(error, "code", default_error_code)


def create_app():
    app = flask.Flask(__name__)
    for code, exception in default_exceptions.items():
        app.errorhandler(code)(_handle_http_exception)
    app.errorhandler(Exception)(_handle_http_exception)  # to handle all exceptions in debug mode
    return app


app = create_app()
db = DatabaseClient()


@app.route("/")
def index():
    return "Just what do you think you're doing, Dave?"


@app.route("/tables", methods=["GET", "POST"])
def tables():
    if flask.request.method == "GET":
        return flask.jsonify({"tables": db.get_table_list()})
    if flask.request.method == "POST":
        input_validation.validate_post_tables(flask.request.json)
        columns = [column_data for column_data in flask.request.json.get("columns", [])]
        table_name = db.create_table(table_name=flask.request.json["table_name"], columns=columns)
        return flask.jsonify({"table_name": table_name})


@app.route("/tables/<table_name>", methods=["DELETE"])
def table(table_name=None):
    input_validation.validate_sql_label(table_name)
    db.delete_table(table_name)
    return "OK"


@app.route("/tables/<table_name>/columns", methods=["GET"])
def table_columns(table_name=None):
    input_validation.validate_sql_label(table_name)
    columns = db.get_columns(table_name)
    return flask.jsonify({"columns": columns})


@app.route("/tables/<table_name>/rows", methods=["GET", "POST"])
def rows(table_name):
    input_validation.validate_sql_label(table_name)
    if flask.request.method == "GET":
        rows = db.get_rows(table_name)
        return flask.jsonify({
            "table_name": table_name,
            "rows": rows
        })
    if flask.request.method == "POST":
        input_validation.validate_put_post_row(flask.request.json)
        columns_and_values = {item["column_name"]: item["value"] for item in flask.request.json}
        new_row = db.add_row(table_name, columns_and_values)
        return flask.jsonify(new_row)


@app.route("/tables/<table_name>/rows/<row_id>", methods=["GET", "DELETE", "PUT"])
def row(table_name, row_id):
    input_validation.validate_sql_label(table_name)
    input_validation.validate_integer(row_id)
    if flask.request.method == "GET":
        row = db.get_row(table_name, row_id)
        if row is None:
            raise NotFound(description="No row with id {}".format(row_id))
        return flask.jsonify(row)
    if flask.request.method == "DELETE":
        db.delete_row(table_name, row_id)
        return "OK"
    if flask.request.method == "PUT":
        input_validation.validate_put_post_row(flask.request.json)
        columns_and_values = {item["column_name"]: item["value"] for item in flask.request.json}
        db.update_row(table_name, row_id, columns_and_values)
        return "OK"


if __name__ == "__main__":
    config = Config()
    app.debug = True
    app.run(host=config.app_host, port=config.app_port)
