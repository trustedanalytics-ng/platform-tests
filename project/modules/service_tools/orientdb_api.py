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

from datetime import datetime
import json

from modules.tap_object_model import Application


class OrientDbApi(object):
    """OrientDB application API."""

    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    TEST_DATABASE = "database_{}".format(TIMESTAMP)
    TEST_CLASS = "class_{}".format(TIMESTAMP)

    PATH_TO_DATABASES = "rest/databases"
    PATH_TO_CLASSES = "rest/databases/{}/classes".format(TEST_DATABASE)
    PATH_TO_RECORDS = "rest/databases/{}/classes/{}/records".format(TEST_DATABASE, TEST_CLASS)

    def __init__(self, app: Application):
        self._app = app

    def database_create(self):
        """Create database."""
        body = {"database_name": self.TEST_DATABASE}
        self._app.api_request(method="POST", path=self.PATH_TO_DATABASES, body=body)
        if "Details" in self.database_get():
            return self.TEST_DATABASE

    def database_delete(self):
        """Drop database."""
        self._app.api_request(method="DELETE", path="{}/{}".format(self.PATH_TO_DATABASES, self.TEST_DATABASE))

    def database_get(self):
        """Get database info."""
        return self._app.api_request(method="GET", path="{}/{}".format(self.PATH_TO_DATABASES, self.TEST_DATABASE))

    def class_create(self):
        """Create class."""
        body = {"class_name": self.TEST_CLASS}
        self._app.api_request(method="POST", path=self.PATH_TO_CLASSES, body=body)
        if "Records" in self.record_get_all():
            return self.TEST_CLASS

    def class_delete(self):
        """Drop class."""
        return self._app.api_request(method="DELETE", path="{}/{}".format(self.PATH_TO_CLASSES, self.TEST_CLASS),
                                     raw=True)

    @staticmethod
    def record():
        """Sample record."""
        return {
            "id": None,
            "key_1": "value_1",
            "key_2": "value_2",
        }

    def record_create(self):
        """Create record."""
        self._app.api_request(method="POST", path=self.PATH_TO_RECORDS, body=self.record())

    def record_get_all(self):
        """
        Get all records.
        :return json like this:
        {
            "Records": [
                "{
                    '@class_20160513_155607_882356':{
                        'id': 1463147190,
                        'key_1': 'value_1',
                        'key_2': 'value_2'
                    },
                    'version':1,
                    'rid':'#11:0'
                }"
            ]
        }
        """
        return self._app.api_request(method="GET", path=self.PATH_TO_RECORDS)

    def extract_record_from_all(self):
        response = self.record_get_all()
        records = json.loads(response["Records"][0].replace("'", '"'))
        return records["@{}".format(self.TEST_CLASS)]

    def record_get_one(self, record_id):
        """Get one record."""
        return self._app.api_request(method="GET", path="{}/{}".format(self.PATH_TO_RECORDS, record_id))

    def record_delete(self, record_id):
        """Delete record."""
        return self._app.api_request(method="DELETE", path="{}/{}".format(self.PATH_TO_RECORDS, record_id))
