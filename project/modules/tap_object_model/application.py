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
import os

import requests
from retry import retry
import yaml

import config
from ..exceptions import UnexpectedResponseError
from ..http_calls import cloud_foundry as cf
from ..http_calls.platform import service_catalog
from ..tap_logger import log_http_request, log_http_response
from ..test_names import generate_test_object_name


class Application(object):

    STATUS = {"restage": "RESTAGING", "start": "STARTED", "stop": "STOPPED"}

    MANIFEST_NAME = "manifest.yml"

    COMPARABLE_ATTRIBUTES = ["name", "guid", "space_guid", "is_running", "is_started"]

    def __init__(self, name, guid, space_guid, state, instances, urls):
        """local_path - directory where application manifest is located"""
        self.name = name
        self.guid = guid
        self.space_guid = space_guid
        self._state = state
        self.instances = instances
        self.urls = tuple(urls)
        self.request_session = requests.session()

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __hash__(self):
        return hash((self.name, self.guid))

    def __lt__(self, other):
        return self.guid < other.guid

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    @property
    def is_started(self):
        if self._state is None:
            return None
        if self._state.upper() == self.STATUS["start"]:
            return True
        return False

    @property
    def is_running(self):
        if self.instances is None:
            return None
        return self.instances[0] > 0

    @classmethod
    def update_manifest(cls, manifest, app_name, bound_services, env):
        manifest["applications"][0]["name"] = app_name
        if bound_services is not None:
            manifest["applications"][0]["services"] = list(bound_services)
        else:
            if "services" in manifest["applications"][0]:
                del manifest["applications"][0]["services"]
        app_env = manifest["applications"][0].get("env", {})
        if env is not None:
            app_env.update(env)
        if config.cf_proxy is not None:
            http_proxy = "http://{}:911".format(config.cf_proxy)
            https_proxy = "https://{}:912".format(config.cf_proxy)
            app_env.update({"http_proxy": http_proxy, "https_proxy": https_proxy})
        if len(app_env) > 0:
            manifest["applications"][0]["env"] = app_env
        return manifest

    @classmethod
    def push(cls, context, space_guid, source_directory, name=None, bound_services=None, env=None):
        """
        Application which will later be pushed to cf.
        source_directory -- where manifest.yml is located
        name -- name of pushed app (will be changed in manifest)
        bound_services -- iterable with bound service names to be included in manifest
        env -- dict with app's env values to be added to manifest
        """
        name = generate_test_object_name(short=True) if name is None else name
        # read manifest
        manifest_path = os.path.normpath(os.path.join(source_directory, cls.MANIFEST_NAME))
        jar_path = source_directory
        with open(manifest_path) as f:
            manifest = yaml.load(f.read())
        if "path" in manifest["applications"][0]:
            jar_path = os.path.join(jar_path, manifest["applications"][0]["path"])

        manifest = cls.update_manifest(manifest, app_name=name, bound_services=bound_services, env=env)
        with open(manifest_path, "w") as f:
            f.write(yaml.dump(manifest))

        try:
            # push application
            cf.cf_push(source_directory, jar_path, name)
        except:
            application = next((app for app in Application.api_get_list(space_guid) if app.name == name), None)
            if application is not None:
                application.cleanup()
            raise

        # retrieve the application - check that push succeeded
        application = next((app for app in Application.api_get_list(space_guid) if app.name == name), None)
        if application is None:
            raise AssertionError("App {} has not been created on the Platform".format(name))
        context.apps.append(application)
        return application

    def api_request(self, path, method="GET", scheme="http", hostname=None, data=None, params=None, body=None):
        """Send a request to application api"""
        hostname = hostname or self.urls[0]
        request = self.request_session.prepare_request(requests.Request(
            method=method.upper(),
            url="{}://{}/{}".format(scheme, hostname, path),
            params=params,
            data=data,
            json=body
        ))
        log_http_request(request, "")
        response = self.request_session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @staticmethod
    def _get_details_from_response(response):
        return {
            "command": response["command"],
            "detected_buildpack": response["detected_buildpack"],
            "disk_quota": response["disk_quota"],
            "domains": sorted(["{}.{}".format(item["host"], item["domain"]["name"]) for item in response["routes"]]),
            "environment_json": response["environment_json"],
            "instances": response["instances"],
            "memory": response["memory"],
            "package_updated_at": response["package_updated_at"],
            "running_instances": response["running_instances"],
            "service_names": sorted([service["name"] for service in response["services"]])
        }

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def api_get_list(cls, space_guid, service_label=None, client=None):
        """Get list of applications from Console / service-catalog API"""
        response = service_catalog.api_get_filtered_applications(space_guid, service_label, client=client)
        applications = []
        for app in response:
            application = cls(name=app["name"], space_guid=space_guid, guid=app["guid"], state=app["state"],
                              urls=app["urls"], instances=(app["running_instances"],))
            applications.append(application)
        return applications

    def api_get_summary(self, client=None):
        response = service_catalog.api_get_app_summary(self.guid, client=client)
        return self._get_details_from_response(response)

    def api_delete(self, cascade=False, client=None):
        service_catalog.api_delete_app(self.guid, cascade=cascade, client=client)

    def cleanup(self):
        self.api_delete()

    def api_restage(self, client=None):
        service_catalog.api_change_app_status(self.guid, self.STATUS["restage"], client=client)

    def api_start(self, client=None):
        service_catalog.api_change_app_status(self.guid, self.STATUS["start"], client=client)

    def api_stop(self, client=None):
        service_catalog.api_change_app_status(self.guid, self.STATUS["stop"], client=client)

    @retry(AssertionError, tries=30, delay=2)
    def ensure_started(self):
        applications = self.api_get_list(self.space_guid)
        application = next((app for app in applications if app.name == self.name), None)
        if application is None:
            raise AssertionError("App does not exist")
        self._state = application._state
        if not self.is_started:
            raise AssertionError("App is not started")

    # -------------------------------- cf api -------------------------------- #

    @classmethod
    def from_cf_api_space_summary_response(cls, response, space_guid):
        applications = []
        for app_data in response["apps"]:
            app = cls(name=app_data["name"], space_guid=space_guid, state=app_data["state"], guid=app_data["guid"],
                      instances=(app_data["running_instances"], app_data["instances"]), urls=tuple(app_data["urls"]))
            applications.append(app)
        return applications

    @classmethod
    def cf_api_get_list_by_space(cls, space_guid):
        """Get list of applications from Cloud Foundry API by space"""
        response = cf.cf_api_space_summary(space_guid)
        return cls.from_cf_api_space_summary_response(response, space_guid)

    @classmethod
    def cf_api_get_list(cls):
        """Get list of applications from Cloud Foundry API"""
        cf_applications = cf.cf_api_get_apps()
        apps = []
        for data in cf_applications:
            app = cls(name=data["entity"]["name"], space_guid=None, state=data["entity"]["state"],
                      guid=data["metadata"]["guid"], instances=(None, data["entity"]["instances"]),
                      urls=data["metadata"]["url"])
            apps.append(app)
        return apps

    def cf_api_get_summary(self):
        response = cf.cf_api_app_summary(self.guid)
        return self._get_details_from_response(response)

    def cf_api_app_is_running(self):
        key = "running_instances"
        summary = self.cf_api_get_summary()
        if key in summary.keys():
            return summary[key] >= 1
        return False

    def cf_api_env(self):
        response = cf.cf_api_get_app_env(self.guid)
        return {
            "VCAP_SERVICES": response["system_env_json"]["VCAP_SERVICES"],
            "VCAP_APPLICATION": response["application_env_json"]["VCAP_APPLICATION"],
            "ENVIRONMENT_JSON": response["environment_json"]
        }

    def get_credentials(self, service_name, i=0):
        env = self.cf_api_env()
        return env["VCAP_SERVICES"][service_name][i]["credentials"]



