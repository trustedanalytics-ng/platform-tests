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

import config
from ..http_client.http_client import HttpClient
from ..exceptions import UnexpectedResponseError
from ..tap_cli import TapCli
from ..http_calls import cloud_foundry as cf
from ..http_calls.platform import service_catalog, api_service
from ..tap_logger import log_http_request, log_http_response
from ..test_names import generate_test_object_name

class Application(object):
    """Application represents application on TAP engine.

    Application class allows pushing, deleting and getting responses from
    applications.
    """
    STATUS = {"failure": "FAILURE",
              "stopped": "STOPPED",
              "stopping": "STOPPING",
              "starting": "STARTING",
              "running": "RUNNING"}

    MANIFEST_NAME = "manifest.json"

    APP_NAME = "name"
    ENV = "env"
    SERVICES = "services"

    RUN_SCRIPT = "run.sh"

    COMPARABLE_ATTRIBUTES = ["name", "app_id", "is_running", "is_started"]

    def __init__(self, name: str, app_id: str, state: str,
                 instances: list, urls: list, org_id: str=None):
        """Class initializer.

        Args:
            name: Name of the application
            app_id: Id of the application
            state: Current state of the application
            instances: Instances that the application uses
            urls: Urls that the application used
            org_id: In which organization the application resides
        """
        self.name = name
        self.app_id = app_id
        self.org_id = org_id
        self._state = state
        self.instances = instances
        self.urls = tuple(urls)
        self.request_session = requests.session()

    @classmethod
    def update_manifest(cls, manifest: dict, app_name: str,
                        bound_services: list, env: list) -> dict:
        """Updates the name in manifest, replaces the required services
        and appends user defined envs.

        Args:
            manifest: The manifest as a json object
            app_name: The new application name to set
            bound_services: Services to that should be already present. This
                            will replace any services that were present in the
                            manifest!
            env: Envs to append.

        Returns:
            Updated manifest
        """
        manifest[cls.APP_NAME] = app_name

        if bound_services != None:
            if cls.SERVICES not in manifest:
                manifest[cls.SERVICES] = []
            manifest[cls.SERVICES] = bound_services
        else:
            if cls.SERVICES in manifest:
                del manifest[cls.SERVICES]

        if env != None:
            if cls.ENV not in manifest:
                manifest[cls.ENV] = {}
            for par in env:
                manifest[cls.ENV][par[0]] = par[1]

        if config.cf_proxy != None:
            if cls.ENV not in manifest:
                manifest[cls.ENV] = {}
            http_proxy = "http://{}:911".format(config.cf_proxy)
            https_proxy = "https://{}:912".format(config.cf_proxy)
            manifest[cls.ENV]["http_proxy"] = http_proxy
            manifest[cls.ENV]["https_proxy"] = https_proxy

        return manifest

    @classmethod
    def push(cls, context, source_directory: str, name: str=None,
             org_id: str=None, bound_services: list=None, env: dict=None):
        """Pushes the application from source directory with provided name,
        services and envs.

        Args:
            context: context object that will store created applications. It is
                     used later to perform a cleanup
            source_directory: dir with application, manifest and run script
            name: Name of the application. If None, name will be generated
            org_id: To which organization the application should be pushed
            bound_services: iterable with bound service names to be included
                            in manifest the manifest
            env: dict with app's env values to be added to manifest

        Returns:
            Created application object
        """
        # Generate a name for the application
        name = generate_test_object_name(short=True) if name is None else name
        # Read the manifest and modify it with name, services and envs
        manifest_path = os.path.normpath(os.path.join(source_directory,
                                                      cls.MANIFEST_NAME))
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        manifest = cls.update_manifest(manifest, app_name=name,
                                       bound_services=bound_services, env=env)

        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        # Push the application
        try:
            # Assume we are already logged in
            TapCli(source_directory).push()
        except:
            apps = Application.api_get_list(org_id)
            application = next((app for app in apps if app.name == name), None)
            if application is not None:
                application.cleanup()
            raise

        # retrieve the application - check that push succeeded
        apps = Application.api_get_list(org_id)
        application = next((app for app in apps if app.name == name), None)

        if application is None:
            raise AssertionError("App {} has not been created on the Platform".format(name))

        context.apps.append(application)
        return application

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
        """Returns true if application has started."""
        return self._state == self.STATUS["running"]

    @property
    def is_stopped(self):
        return self._state.upper() == self.STATUS["stopped"]

    @property
    def is_running(self):
        """Returns true if any of the application instances are running."""
        return self._state == self.STATUS["running"]

    def api_request(self, path, method="GET", scheme="http", hostname=None, data=None, params=None, body=None,
                    raw=False):
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
        if raw is True:
            return response
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
    def api_get_list(cls, org_id: str=None, client: HttpClient=None):
        """Get list of applications from Console / service-catalog API"""
        response = api_service.get_applications(client=client,
                                                org_id=org_id).json()
        applications = []
        for app in response:
            application = cls(name=app["name"], app_id=app["id"],
                              org_id=app.get("org_id"), state=app["state"],
                              urls=app["urls"], instances=(app["running_instances"]))
            applications.append(application)
        return applications

    def api_get_summary(self, client=None):
        response = service_catalog.api_get_app_summary(self.guid, client=client)
        return self._get_details_from_response(response)

    def api_delete(self, client: HttpClient=None):
        """Deletes the application from tap

        Args:
            client: HttpClient to use
        """
        api_service.delete_application(app_id=self.app_id, client=client)

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
        assert application is not None, "App does not exist"
        self._state = application._state
        assert self.is_started is True, "App is not started"

    @retry(AssertionError, tries=30, delay=2)
    def ensure_stopped(self):
        applications = self.api_get_list(self.space_guid)
        application = next((app for app in applications if app.name == self.name), None)
        assert application is not None, "App does not exist"
        self._state = application._state
        assert self.is_stopped is True, "App is not stopped"

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
