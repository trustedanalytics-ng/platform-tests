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

from retry import retry

from modules.exceptions import UnexpectedResponseError
from modules.http_calls import kubernetes
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.tap_logger import get_logger
from modules.tap_object_model.api_service import ApiService
from tests.fixtures.assertions import assert_returns_http_success_with_retry

@functools.total_ordering
class K8sApplication(object):
    # TODO Merge with Application

    STATE_RUNNING = "RUNNING"
    STATE_STOPPED = "STOPPED"
    STATE_FAILURE = "FAILURE"
    COMPARABLE_ATTRIBUTES = ["id", "name", "state", "urls", "replication", "image_state"]
    logger = get_logger(__name__)

    def __init__(self, instance_id: str, name: str, state: str, urls: list, replication: int, image_state: str):
        self.id = instance_id
        self.name = name
        self.state = state
        self.urls = tuple(urls)
        self.replication = replication
        self.image_state = image_state

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self.COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{} (id={})".format(self.__class__.__name__, self.id)

    @classmethod
    def update_manifest(cls, file_path, updated_params):
        with open(file_path) as f:
            manifest_json = json.loads(f.read())
        for key, val in updated_params.items():
            manifest_json[key] = val
        cls.logger.debug("Manifest: {}\n".format(manifest_json))
        with open(file_path, "w") as f:
            f.write(json.dumps(manifest_json))

    @classmethod
    def push(cls, context, file_path, manifest_path):
        assert file_path is not None, "File path is not set"
        assert manifest_path is not None, "Manifest path is not set"
        response = ApiService.push_application(file_path, manifest_path).json()
        new_app = cls.ensure_created(response["name"])
        context.k8s_apps.append(new_app)
        return new_app

    @classmethod
    def get(cls, instance_id):
        response = ApiService.get_application(instance_id)
        instance = cls._from_response(response.json())
        return instance

    @classmethod
    def get_list(cls):
        response = ApiService.get_applications().json()
        apps = []
        for item in response:
            app = cls._from_response(item)
            apps.append(app)
        return apps

    @classmethod
    @retry(AssertionError, tries=20, delay=10)
    def ensure_created(cls, name):
        apps = cls.get_list()
        app = next((a for a in apps if a.name == name), None)
        assert app is not None, "Application {} was not created".format(name)
        return app

    @retry(AssertionError, tries=12, delay=5)
    def ensure_running(self):
        apps = self.get_list()
        app = next((a for a in apps if a.id == self.id), None)
        assert app is not None, "Application does not exist"
        self.state = app.state
        self.urls = app.urls
        assert self.state == self.STATE_RUNNING, "App state is not running, it's {}".format(self.state)

    @retry(AssertionError, tries=12, delay=5)
    def ensure_stopped(self):
        apps = self.get_list()
        app = next((a for a in apps if a.id == self.id), None)
        assert app is not None, "Application does not exist"
        self.state = app.state
        assert self.state == self.STATE_STOPPED, "App state is not stopped, it's {}".format(self.state)

    def get_http_client(self, url):
        client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=url))
        return client

    def send_request(self, path=""):
        assert self.urls is not None, "Application url is not set"
        client = self.get_http_client(self.urls[0])
        response = client.request(
            method=HttpMethod.GET,
            path=path,
            raw_response=True,
            raise_exception=True,
            msg="K8sApplication: get /{}".format(path)
        )
        return response

    @retry(AssertionError, tries=20, delay=5)
    def ensure_ready(self):
        assert_returns_http_success_with_retry(self.send_request)

    @retry(AssertionError, tries=20, delay=5)
    def ensure_is_down(self):
        try:
            self.send_request()
        except UnexpectedResponseError as e:
            assert e.status // 100 == 5

    def check_healthz(self):
        response = self.send_request("healthz")
        return response

    def delete(self):
        ApiService.delete_application(self.id)

    def cleanup(self):
        self.delete()

    def scale(self, replicas):
        response = ApiService.scale_application(self.id, replicas)
        assert response["message"] == "success"

    def stop(self):
        response = ApiService.stop_application(self.id)
        assert response["message"] == "success"

    def start(self):
        response = ApiService.start_application(self.id)
        assert response["message"] == "success"

    def get_logs(self):
        response = ApiService.get_application_logs(self.id)
        return response

    def get_pods(self):
        response = kubernetes.k8s_get_pods()
        all_pod_metadata = [i["metadata"] for i in response["items"]]
        this_app_pod_metadata = []
        for pod_metadata in all_pod_metadata:
            if pod_metadata["labels"].get("instance_id") == self.id:
                this_app_pod_metadata.append(pod_metadata)
        return this_app_pod_metadata

    @classmethod
    def _from_response(cls, response):
        return cls(instance_id=response["id"], name=response["name"], state=response["state"], urls=response["urls"],
                   replication=response["replication"], image_state=response["imageState"])
