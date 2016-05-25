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

import functools
import json

import requests

from configuration import config
from ..exceptions import UnexpectedResponseError
from ..tap_logger import get_logger, log_http_request, log_http_response
from ..test_names import generate_test_object_name

logger = get_logger(__name__)


@functools.total_ordering
class ArcadiaDataSet(object):

    COMPARABLE_ATTRIBUTES = ["ds_id", "name", "ds_type"]

    def __init__(self, ds_id, name, ds_type, dc_name):
        self.ds_id = ds_id
        self.name = name
        self.ds_type = ds_type
        self.dc_name = dc_name

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.ds_id < other.ds_id

    def __repr__(self):
        return "{0} (title={1}, ds_id={2})".format(self.__class__.__name__, self.name, self.ds_id)


class ArcadiaDataConnection(object):

    def __init__(self, dc_id, name, dc_type):
        self.dc_id = dc_id
        self.name = name
        self.dc_type = dc_type

    def __repr__(self):
        return "{0} (title={1}, dc_id={2})".format(self.__class__.__name__, self.name, self.dc_id)


class Arcadia(object):
    TEST_DATASETS = []

    def __init__(self, username=config.CONFIG["arcadia_username"], password=config.CONFIG["arcadia_password"]):
        self.username = username
        self.password = password
        self.url = "http://arcadia.{}/".format(config.CONFIG["domain"])
        self.http_session = requests.Session()
        self.csrf_token = None
        self.login()
        self.data_connection = next(ds for ds in self.get_data_connection_list() if ds.name == "arcadia")

    def __repr__(self):
        return "{} (instance_url={})".format(self.__class__.__name__, self.url)

    def _request(self, method, endpoint, body=None, data=None, params=None, headers=None, message_on_error=""):
        data = data or {}
        if self.csrf_token is not None:
            headers = {"X-CSRFToken": self.csrf_token}
        request = requests.Request(
            method=method,
            url=self.url + endpoint,
            data=data,
            params=params,
            json=body,
            headers=headers
        )
        request = self.http_session.prepare_request(request)
        log_http_request(request, username=self.username, password=self.password)
        response = self.http_session.send(request)
        log_http_response(response)
        self.csrf_token = response.cookies.get('csrftoken', self.csrf_token)
        if not response.ok:
            raise UnexpectedResponseError(status=response.status_code, error_message=message_on_error)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    def login(self):
        self._request(
            method="GET",
            endpoint="arc/apps/login",
            message_on_error="Failed to get token from Arcadia"
        )
        self._request(
            method="POST",
            endpoint="arc/apps/login",
            data={"username": self.username, "password": self.password, "csrfmiddlewaretoken": self.csrf_token},
            headers={"X_CSRFToken": self.csrf_token},
            message_on_error="Failed login to Arcadia"
        )

    @staticmethod
    def _from_response(response):
        data_sets = []
        for data in response:
            data_set = ArcadiaDataSet(ds_id=data["id"], name=data["name"], ds_type=data["type"],
                                      dc_name=data["dc_name"])
            data_sets.append(data_set)
        return data_sets

    def _delete_dataset(self, dataset):
        """DELETE /arc/datasets/dataset/{id}"""
        params = {"delete_table": False}
        self._request(method="DELETE", endpoint="arc/datasets/dataset/{}".format(dataset.ds_id), params=params,
                      message_on_error="Couldn't delete dataset")

    def _post_sqlrun_jsonselect(self, dc_id, type, cache_read=False, db_name=None):
        """POST /arc/sqlrun/jsonselect"""
        dataset_requirements = {
            "version": 1,
            "type": type,
            "time": [],
            "session": [],
            "dimensions": [],
            "aggregates": [],
            "filters": [],
            "having": [],
            "global_segments": [],
            "events": [],
            "distinct": "false"
        }
        if db_name is not None:
            dataset_requirements.update({"dbname": db_name})
        data = {
            "query": "",
            "dataconnection_id": dc_id,
            "cache_read": cache_read,
            "dsreq": json.dumps(dataset_requirements)
        }
        return self._request(method="POST", endpoint="arc/sqlrun/jsonselect", data=data,
                             message_on_error="Couldn't process jsonselect")

    def create_dataset(self, org_name, dataset_name, arcadia_dataset_name=None,
                       dataset_type="singletable"):
        """POST /arc/datasets/dataset"""
        test_name = generate_test_object_name() or arcadia_dataset_name
        dataset_detail = "{}.{}".format(org_name, dataset_name)
        data = {
            "dataconnection_id": self.data_connection.dc_id,
            "dataset_name": test_name,
            "dataset_type": dataset_type,
            "dataset_detail": dataset_detail,
            "dataset_info": ""
        }
        response = self._request(method="POST", endpoint="arc/datasets/dataset", data=data,
                                 message_on_error="Couldn't create dataset")
        new_dataset = next((ds for ds in self._from_response(response) if ds.name == test_name), None)
        if new_dataset is None:
            raise AssertionError("New dataset was not created in arcadia")
        self.TEST_DATASETS.append(new_dataset)
        return new_dataset

    def get_dataset_list(self):
        response = self._request(method="GET", endpoint="arc/datasets/dataset", message_on_error="ARCADIA: get dataset")
        return [ds for ds in self._from_response(response) if ds.dc_name == self.data_connection.name]

    def delete_dataset(self, dataset):
        self._delete_dataset(dataset)
        self.TEST_DATASETS.remove(dataset)

    def teardown_test_datasets(self):
        while len(self.TEST_DATASETS) > 0:
            dataset = self.TEST_DATASETS.pop()
            try:
                self._delete_dataset(dataset)
            except UnexpectedResponseError:
                logger.warning("Failed to delete {}".format(dataset))

    def get_data_connection_list(self):
        response = self._request(method="GET", endpoint="arc/datasets/dataconnection",
                                 message_on_error="Couldn't get dataconnection")
        data_connections = []
        for data in response:
            data_connection = ArcadiaDataConnection(dc_id=data["id"], name=data["name"], dc_type=data["type"])
            data_connections.append(data_connection)
        return data_connections

    def get_database_list(self):
        response = self._post_sqlrun_jsonselect(self.data_connection.dc_id, ".databases")
        db_list = []
        for db in response["rows"]:
            db_list.append(db[0])
        return db_list

    def get_table_list(self, dbname):
        response = self._post_sqlrun_jsonselect(self.data_connection.dc_id, ".tables", db_name=dbname)
        table_list = []
        for table in response["rows"]:
            table_list.append(table[0])
        return table_list
