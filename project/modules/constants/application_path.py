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


class ApplicationPath(object):
    """Paths to directories with applications."""

    BASE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "applications")
    ORIENTDB_API = os.path.join(BASE_PATH, "orientdb-api")
    MONGODB_API = os.path.join(BASE_PATH, "mongodb-api")
    SAMPLE_APPS_PATH = os.path.join(BASE_PATH, "sample-apps")
    SQL_API_EXAMPLE = os.path.join(BASE_PATH, "sql-api-example")
    SAMPLE_PYTHON_APP = os.path.join(SAMPLE_APPS_PATH, "sample-python-app")
    SAMPLE_PYTHON_APP_TAR = os.path.join(SAMPLE_PYTHON_APP, "app.tar.gz")
    SAMPLE_JAVA_APP = os.path.join(SAMPLE_APPS_PATH, "sample-java-application")
    SAMPLE_JAVA_APP_TAR = os.path.join(SAMPLE_JAVA_APP, "app.tar.gz")

