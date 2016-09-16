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
from ..http_client.configuration_provider.console import ConsoleConfigurationProvider
from ..http_client import HttpClientFactory


class Application(object):
    """ Application represents an Application on TAP.
    It allows to push, delete, retrieve TAP applications using `console` or
    `api-service` REST APIs.
    It enables sending http requests to such applications.
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

    COMPARABLE_ATTRIBUTES = ["name", "app_id", "is_running"]

    def __init__(self, name: str, app_id: str, state: str,
                 instances: list, urls: list, org_id: str=None,
                 client: HttpClient=None):
        """Class initializer.

        Args:
            name: Name of the application
            app_id: Id of the application
            state: Current state of the application
            instances: Instances that the application uses
            urls: Urls that the application used
            org_id: In which organization the application resides
            client: The Http client to use. If None, Http client from default
                    configuration will be used
        """
        self.name = name
        self.app_id = app_id
        self.org_id = org_id
        self._state = state
        self.instances = instances
        self.urls = tuple(urls)
        if client is None:
            self._client = self._get_default_client()
        else:
            self._client = client
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
             org_id: str=None, bound_services: list=None, env: dict=None,
             client: HttpClient=None):
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
            client: The Http client to use. If None, default (admin via console)
                    will be used.

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
            apps = Application.get_list(org_id, client)
            application = next((app for app in apps if app.name == name), None)
            if application is not None:
                application.cleanup()
            raise

        # retrieve the application - check that push succeeded
        apps = Application.get_list(org_id, client)
        application = next((app for app in apps if app.name == name), None)

        if application is None:
            raise AssertionError("App {} has not been created on the Platform".format(name))

        context.apps.append(application)
        return application

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __hash__(self):
        return hash((self.name, self.app_id))

    def __lt__(self, other):
        return self.app_id < other.app_id

    def __repr__(self):
        return "{0} (name={1}, app_id={2})".format(self.__class__.__name__, self.name, self.app_id)

    @property
    def is_stopped(self) -> bool:
        """Returns true if application has stopped."""
        return self._state.upper() == self.STATUS["stopped"]

    @property
    def is_running(self) -> bool:
        """Returns true if any of the application instances are running."""
        return self._state == self.STATUS["running"]

    def api_request(self, path: str, method: str="GET", scheme: str="http",
                    hostname: str=None, data: dict=None, params: dict=None,
                    body: dict=None, raw: bool=False):
        """Send a request to application api

        Args:
            path: This is where the application resides
            method: What REST method should be used
            scheme: Should http or https be used?
            hostname: This is the full url of the application
            data: Data that will be the json_body of the request
            params: Parameters tha will be the params of the request
            body: Body to be put into the request
            raw: Should raw response be returned or not

        Returns:
            Response to the request
        """
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
    def _get_details_from_response(response: dict) -> dict:
        """Truncates the response to interesting attributes and returns it

        Returns:
            Truncated response of interesting attributes
        """
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

    @staticmethod
    def _get_default_client():
        """Retrieves the default Http Client from configuration.

        Returns:
            Default Http Client (admin for console)
        """
        configuration = ConsoleConfigurationProvider.get()
        return HttpClientFactory.get(configuration)

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def get_list(cls, org_id: str=None, client: HttpClient=None):
        """Get list of applications from Console / service-catalog API

        Args:
            org_id: Organization id from which the application will be listed
            client: Http client to use
        """
        if client is None:
            client = cls._get_default_client()
        response = api_service.get_applications(client=client,
                                                org_id=org_id).json()
        applications = []
        for app in response:
            application = cls(name=app["name"], app_id=app["id"],
                              org_id=app.get("org_id"), state=app["state"],
                              urls=app["urls"], instances=(app["running_instances"]),
                              client=client)
            applications.append(application)
        return applications

    def get(self) -> dict:
        """Returns the details of the uploaded application.

        Returns:
            Application details
        """
        response = api_service.get_application(self._client, self.app_id)
        return self._get_details_from_response(response)

    def delete(self):
        """Deletes the application from tap
        """
        api_service.delete_application(self._client, self.app_id)

    def cleanup(self):
        """Deletes the application from tap
        """
        self.delete()

    def api_start(self):
        """Sends the start command to application
        """
        api_service.start_application(self._client, self.app_id)

    def api_stop(self):
        """Sends the stop command to application
        """
        api_service.stop_application(self._client, self.app_id)

    def _update_state(self):
        """Updates the state of the application. If the application is
        not present, assertion kicks in
        """
        applications = self.get_list(self.org_id, self._client)
        application = next((app for app in applications if app.name == self.name), None)
        assert application is not None, "App does not exist"
        self._state = application._state


    @retry(AssertionError, tries=30, delay=2)
    def ensure_running(self):
        """Waits for the application to start for a given ammount of tries.

        If the application hasn't started, assertion kicks in
        """
        self._update_state()
        assert self.is_running is True, "App is not started"

    @retry(AssertionError, tries=30, delay=2)
    def ensure_stopped(self):
        """Waits for the application to stop for a given ammount of tries.

        If the application hasn't stopped, assertion kicks in
        """
        self._update_state()
        assert self.is_stopped is True, "App is not stopped"
