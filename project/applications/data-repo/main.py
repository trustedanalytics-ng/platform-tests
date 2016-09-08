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

import os

import flask


app = flask.Flask(__name__)


@app.route("/files/<path:filename>")
def download_file(filename):
    return flask.send_from_directory(
        os.path.join(os.path.dirname(__file__), 'files'),
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app_port = int(os.environ.get("PORT", "80"))
    app_host = "0.0.0.0"
    app.debug = True
    app.run(host=app_host, port=app_port)
