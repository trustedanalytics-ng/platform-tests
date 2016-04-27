#!/usr/bin/env python3

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

from bson.objectid import ObjectId
import flask
import flask_restful
import pymongo

from config import AppConfig
from model import TestSuiteModel
from runner import Runner


app = flask.Flask(__name__)
api = flask_restful.Api(app)

runner = Runner()


class ExceptionHandlingApi(flask_restful.Api):

    def handle_error(self, e):
        code = getattr(e, "code", 500)
        message = getattr(e, "description", "Internal Server Error")
        if hasattr(e, "data"):
            message = e.data.get("message")
        response = {"message": message, "status": code}
        return self.make_response(response, code)


class TestSuite(flask_restful.Resource):

    @staticmethod
    def _validate_credentials(username, password, minimal_len=1):
        if len(username) < minimal_len or len(password) < minimal_len:
            raise ValueError()

    def get(self):
        """Return a list of test suites."""
        all_suites = [s.to_dict() for s in TestSuiteModel.get_list()]
        return flask.Response(json.dumps(all_suites), mimetype="application/json")

    def post(self):
        """
        Check whether runner is busy
        if so, return 429
        else, call Runner.run
        return suite id from Runner.run
        """
        if runner.is_busy:
            flask_restful.abort(429, message="Runner is busy")

        username = password = None
        try:
            request_body = json.loads(flask.request.data.decode())
            username = request_body["username"]
            password = request_body["password"]
            self._validate_credentials(username, password)
        except (ValueError, KeyError):
            flask_restful.abort(400, message="Bad request")

        new_suite = runner.run(username=username, password=password)
        return flask.jsonify(new_suite.to_dict())


class TestSuiteResults(flask_restful.Resource):
    def get(self, suite_id):
        """Return detailed results of one test suite."""
        suite = None
        try:
            suite = TestSuiteModel.get_by_id(suite_id=ObjectId(suite_id))
        except (pymongo.errors.InvalidId, TypeError):
            flask_restful.abort(404, message="Not found")
        return flask.jsonify(suite.to_dict())


if __name__ == "__main__":
    config = AppConfig()
    api = ExceptionHandlingApi(app, catch_all_404s=True)
    api.add_resource(TestSuite, "/rest/platform_tests/testsuites")
    api.add_resource(TestSuiteResults, "/rest/platform_tests/testsuites/<suite_id>/results")

    app.run(host=config.hostname, port=config.port, debug=config.debug)
