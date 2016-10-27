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

import re

import jsonschema
from werkzeug.exceptions import BadRequest


POST_TABLES_SCHEMA = {
    "type": "object",
    "properties": {
        "table_name": {"type": "string"},
        "columns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "is_nullable": {"type": "boolean"},
                    "max_len": {"type": "integer"}
                },
                "additionalProperties": False,
                "required": ["name", "type"]
            },
            "minItems": 1
        }
    },
    "additionalProperties": False,
    "required": ["table_name", "columns"]
}


_COLUMN_SCHEMA = {
    "type": "object",
    "properties": {
        "column_name": {"type": "string"},
        "value": {"type": ["string", "integer", "number", "boolean", "null"]}
    },
    "required": ["column_name", "value"],
    "additionalProperties": False
}


POST_PUT_ROWS_SCHEMA = {
    "type": "array",
    "items": _COLUMN_SCHEMA,
    "minItems": 1
}



def validate_sql_label(user_provided_string):
    """
    To be used on user-provided strings which serve as labels (table names, column names).
    Raise BadRequest exception if user_provided_string does not match ^([a-zA-Z0-9]|_){1,255}$.
    """
    pattern = "^([a-zA-Z0-9]|_){1,63}$"
    if not re.match(pattern, user_provided_string):
        raise BadRequest("DB labels can consist of 1 to 63 alphanumeric characters and '_'.")


def validate_sql_data_type(user_provided_string):
    """
    To be used in user-provided table definitions.
    Raise an exception if user_provided_string is not a valid postgresql data type.
    """
    pattern = "^([a-zA-Z0-9]|\s|_){3,63}$"
    if not re.match(pattern, user_provided_string):
        raise BadRequest("Incorrect sql data type")


def validate_integer(user_provided_string):
    pattern = "^\d+$"
    if not re.match(pattern, user_provided_string):
        raise BadRequest("{} is not an integer".format(user_provided_string))


def validate_post_tables(json_body):
    try:
        jsonschema.validate(json_body, POST_TABLES_SCHEMA)
    except jsonschema.ValidationError:
        raise BadRequest("Invalid body")
    validate_sql_label(json_body["table_name"])
    for col_data in json_body.get("columns", []):
        validate_sql_label(col_data["name"])
        validate_sql_data_type(col_data["type"])


def validate_put_post_row(json_body):
    try:
        jsonschema.validate(json_body, POST_PUT_ROWS_SCHEMA)
    except jsonschema.ValidationError:
        raise BadRequest("Invalid body")
    for item in json_body:
        validate_sql_label(item["column_name"])

