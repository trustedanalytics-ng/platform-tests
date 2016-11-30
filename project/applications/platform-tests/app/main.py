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
import logging
import sys

from bson.objectid import ObjectId
import flask
import flask_restful
import pymongo

from .config import AppConfig
from .console_authenticator import AuthenticationException, ConsoleAuthenticator
from .model import TestSuiteModel
from .runner import Runner
from .suite_provider import SuiteProvider

logger = logging.getLogger(__name__)

app = flask.Flask(__name__)
app_config = AppConfig()


class ExceptionHandlingApi(flask_restful.Api):
    def handle_error(self, e):
        code = getattr(e, "code", 500)

        # code in [13, 18] when mongodb authorization fails
        if code >= 500 or code < 200:
            app.log_exception(sys.exc_info())

        message = getattr(e, "description", "Internal Server Error")
        if hasattr(e, "data"):
            message = e.data.get("message")
        response = {"message": message, "status": code}
        return self.make_response(response, code)


class Test(flask_restful.Resource):
    runner = Runner()
    console_authenticator = ConsoleAuthenticator(tap_domain=app_config.tap_domain)

    def get(self):
        """Return a list of performed tests."""
        all_suites = [s.to_dict() for s in TestSuiteModel.get_list()]
        return flask.Response(json.dumps(all_suites), mimetype="application/json")

    def post(self):
        """
        Check whether runner is busy
        if so, return 429
        else, call Runner.run
        return test id from Runner.run
        """
        if self.runner.is_busy:
            flask_restful.abort(429, message="Runner is busy")

        username = password = None
        try:
            request_body = json.loads(flask.request.data.decode())
            username = request_body["username"]
            password = request_body["password"]
        except (ValueError, KeyError):
            flask_restful.abort(400, message="Bad request")
        try:
            self.console_authenticator.authenticate(username, password)
        except AuthenticationException:
            flask_restful.abort(401, message="Incorrect credentials")

        new_suite = self.runner.run(username=username, password=password)
        return flask.jsonify(new_suite.to_dict())


class TestResult(flask_restful.Resource):
    def get(self, test_id):
        """Return detailed results of one test."""
        suite = None
        try:
            suite = TestSuiteModel.get_by_id(suite_id=ObjectId(test_id))
        except (pymongo.errors.InvalidId, TypeError):
            flask_restful.abort(404, message="Not found")
        return flask.jsonify(suite.to_dict())


class TestSuite(flask_restful.Resource):
    def get(self):
        """Return a list of available test suites."""
        last_runs = TestSuiteModel.get_last_five()
        suites = SuiteProvider.get_list(last_runs)
        return flask.Response(json.dumps(suites), mimetype="application/json")


def start():
    options = {"host": app_config.hostname, "port": app_config.port, "debug": app_config.debug}
    logger.info("Starting server %s", options)
    app.run(**options)


api = ExceptionHandlingApi(app, catch_all_404s=True)
api.add_resource(Test, "/rest/platform_tests/tests")
api.add_resource(TestResult, "/rest/platform_tests/tests/<test_id>/results")
api.add_resource(TestSuite, "/rest/platform_tests/tests/suites")
