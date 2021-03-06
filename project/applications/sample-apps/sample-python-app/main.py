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
"""This is a basic python application. Upon entering '/' it will return
   some text in your web browser."""


import os

import flask

APP = flask.Flask(__name__)
APP_PORT = int(os.environ.get("PORT", "80"))
APP_HOST = "0.0.0.0"
APP.debug = True


@APP.route("/")
def index():
    """This is returned upon entering /
    """
    return "Test app"

if __name__ == "__main__":
    APP.run(host=APP_HOST, port=APP_PORT)
