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

from configuration.config import CONFIG
from ..exceptions import UnexpectedResponseError
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from ..http_client.http_client import HttpClient
from ..http_client.http_client_factory import HttpClientFactory
from ..tap_logger import get_logger
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
    """Arcadia service instance."""

    TEST_DATASETS = []

    def __init__(self, username=CONFIG["arcadia_username"], password=CONFIG["arcadia_password"]):
        self.client = None
        self.csrf_token = None
        self.username = username
        self.password = password
        self.url = "http://arcadia.{}/".format(CONFIG["domain"])
        self.login()
        self.data_connection = next(ds for ds in self.get_data_connection_list() if ds.name == "arcadia")

    def __repr__(self):
        return "{} (instance_url={})".format(self.__class__.__name__, self.url)

    def login(self):
        self._request(
            method=HttpMethod.GET,
            path="arc/apps/login",
            msg="Arcadia: login form"
        )
        self._request(
            method=HttpMethod.POST,
            path="arc/apps/login",
            data={
                "username": self.username,
                "password": self.password,
                "csrfmiddlewaretoken": self.csrf_token,
            },
            msg="Arcadia: login"
        )

    def create_dataset(self, org_name, dataset_name, arcadia_dataset_name=None, dataset_type="singletable"):
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
        response = self._request(
            method=HttpMethod.POST,
            path="arc/datasets/dataset",
            data=data,
            msg="Arcadia: create dataset"
        )
        new_dataset = next((ds for ds in self._from_response(response) if ds.name == test_name), None)
        if new_dataset is None:
            raise AssertionError("New dataset was not created in arcadia")
        self.TEST_DATASETS.append(new_dataset)
        return new_dataset

    def get_dataset_list(self):
        response = self._request(
            method=HttpMethod.GET,
            path="arc/datasets/dataset",
            msg="Arcadia: get dataset"
        )
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
        response = self._request(
            method=HttpMethod.GET,
            path="arc/datasets/dataconnection",
            msg="Arcadia: get dataconnection"
        )
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

    def get_client(self) -> HttpClient:
        """Return jupyter http client."""
        if self.client is None:
            self.client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(
                url=self.url,
                username=self.username,
                password=self.password
            ))
        return self.client

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
        self._request(
            method=HttpMethod.DELETE,
            path="arc/datasets/dataset/{}".format(dataset.ds_id),
            params={"delete_table": False},
            msg="Arcadia: delete dataset"
        )

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
        return self._request(
            method=HttpMethod.POST,
            path="arc/sqlrun/jsonselect",
            data=data,
            msg="Arcadia: process jsonselect",
        )

    def _get_headers(self):
        """Get request headers."""
        headers = None
        if self.csrf_token is not None:
            headers = {"X-CSRFToken": self.csrf_token}
        return headers

    def _request(self, method: HttpMethod, path, params=None, data=None, body=None, msg=""):
        """Send request to arcadia instance."""
        response = self.get_client().request(
            method=method,
            path=path,
            headers=self._get_headers(),
            params=params,
            data=data,
            body=body,
            msg=msg,
            raw_response=True
        )
        if not response.ok:
            raise UnexpectedResponseError(status=response.status_code, error_message=response.text)
        self.csrf_token = response.cookies.get('csrftoken', self.csrf_token)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text
