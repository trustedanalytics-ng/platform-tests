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
import os


app = flask.Flask(__name__)


@app.route("/")
def index():
    return "Test app"


if __name__ == "__main__":
    VCAP_APP_PORT = "VCAP_APP_PORT"
    app_port = int(os.environ.get(VCAP_APP_PORT, "8080"))
    app_host = "0.0.0.0"
    app.debug = True
    app.run(host=app_host, port=app_port)
