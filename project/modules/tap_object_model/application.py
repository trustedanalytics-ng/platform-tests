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

from modules.constants import TapEntityState
from modules.exceptions import UnexpectedResponseError
import modules.http_calls.platform.api_service as api
from modules.http_client import HttpClient
from modules.tap_cli import TapCli
from modules.tap_logger import log_http_request, log_http_response
from ._api_model_superclass import ApiModelSuperclass


class Application(ApiModelSuperclass):
    """ Application represents an Application on TAP.
    It allows to push, delete, retrieve TAP applications using 'console' or 'api-service' REST APIs.
    It enables sending http requests to such applications.
    """

    _COMPARABLE_ATTRIBUTES = ["name", "id", "image_type", "_state", "replication", "running_instances", "urls"]
    _REFRESH_ATTRIBUTES = ["id", "image_type", "_state", "replication", "running_instances", "urls"]

    MANIFEST_NAME = "manifest.json"

    def __init__(self, app_id: str, name: str, bindings: list, image_type: str, state: str, replication: int,
                 running_instances: int, urls: list, client: HttpClient=None):
        """Class initializer.

        Args:
            name: Name of the application
            id: Id of the application
            state: Current state of the application
            instances: Instances that the application uses
            urls: Urls that the application used
            client: The Http client to use. If None, Http client from default
                    configuration will be used
        """
        super().__init__(item_id=app_id, client=client)
        self.name = name
        self.bindings = bindings
        self.image_type = image_type
        self._state = state
        self.replication = replication
        self.running_instances = running_instances
        self.urls = tuple(urls)
        self._request_session = requests.session()

    def __repr__(self):
        return "{} (name={}, id={})".format(self.__class__.__name__, self.name, self.id)

    @classmethod
    def update_manifest(cls, manifest_path: str, params: dict):
        """Updates the manifest with provided params

        Args:
            manifest_path: Path to the manifest file
            params: key->value that will update the manifest
        """
        with open(manifest_path, 'r') as file:
            manifest = json.loads(file.read())
            for key, val in params.items():
                manifest[key] = val

        with open(manifest_path, 'w') as file:
            file.write(json.dumps(manifest))

    @classmethod
    def push(cls, context, app_dir: str, tap_cli: TapCli, client: HttpClient=None):
        """Pushes the application from source directory with provided name,
        services and envs. This only pushed the application, but does not
        verify whether the app is running or not.

        Args:
            context: context object that will store created applications. It is used later to perform a cleanup.
            app_dir: path to the gzipped application
            tap_cli: tap client, that will be used to push the app.
            client: The Http client to use. If None, default (admin via console)
                    will be used. It will be used to verify if the app was pushed

            Returns:
                Created application object
        """
        name = cls._read_app_name_from_manifest(app_dir)
        tap_cli.login()
        try:
            tap_cli.push(app_dir)
        except:
            apps = Application.get_list(client=client)
            application = next((app for app in apps if app.name == name), None)
            if application is not None:
                application.cleanup()
            raise

        # Find the application and return it
        apps = Application.get_list(client=client)
        app = next((a for a in apps if a.name == name), None)
        assert app is not None, "App {} has not been created on the platform".format(name)

        # Wait for the application to receive id
        app._ensure_has_id()
        context.apps.append(app)
        return app

    @property
    def is_stopped(self) -> bool:
        """Returns True if application is stopped."""
        return self._state.upper() == TapEntityState.STOPPED

    @property
    def is_running(self) -> bool:
        """Returns True if any of the application instances are running."""
        return self._state == TapEntityState.RUNNING

    @classmethod
    def get(cls, app_id: str, client: HttpClient=None):
        """Retrieves the application based on app id

        Args:
            id: id of the application to retrieve

        Returns:
            The application
        """
        if client is None:
            client = cls._get_default_client()
        response = api.get_application(app_id=app_id, client=client)
        return cls._from_response(response, client)

    @classmethod
    def get_list(cls, client: HttpClient=None):
        """Get list of applications from Console / service-catalog API

        Args:
            client: Http client to use
        """
        if client is None:
            client = cls._get_default_client()
        response = api.get_applications(client=client).json()
        return cls._list_from_response(response, client)

    def delete(self, client: HttpClient=None):
        """ Deletes the application from TAP """
        client = self._get_client(client)
        api.delete_application(app_id=self.id, client=client)

    def start(self, client: HttpClient=None):
        """ Sends the start command to application """
        client = self._get_client(client)
        api.start_application(app_id=self.id, client=client)

    def stop(self, client: HttpClient=None):
        """ Sends the stop command to application """
        client = self._get_client(client)
        api.stop_application(app_id=self.id, client=client)

    @retry(AssertionError, tries=30, delay=2)
    def ensure_running(self):
        """Waits for the application to start for a given number of tries.

        If the application hasn't started, assertion kicks in
        """
        self._refresh()
        assert self.is_running is True, "App {} is not started. App's state: {}".format(self.name, self._state)

    @retry(AssertionError, tries=30, delay=2)
    def ensure_stopped(self):
        """Waits for the application to stop for a given number of tries.

        If the application hasn't stopped, assertion kicks in
        """
        self._refresh()
        assert self.is_stopped is True, "App {} is not stopped. App's state: {}".format(self.name, self._state)

    def api_request(self, path: str, method: str="GET", scheme: str="http", hostname: str=None, data: dict=None,
                    params: dict=None, body: dict=None, raw: bool=False):
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
        request = self._request_session.prepare_request(requests.Request(
            method=method.upper(),
            url="{}://{}/{}".format(scheme, hostname, path),
            params=params,
            data=data,
            json=body
        ))
        log_http_request(request, "")
        response = self._request_session.send(request)
        log_http_response(response)
        if raw is True:
            return response
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        return cls(app_id=response["id"], name=response["name"], bindings=response["bindings"],
                   image_type=response["imageType"], state=response["state"], replication=response["replication"],
                   running_instances=response["running_instances"], urls=response["urls"], client=client)

    @classmethod
    def _read_app_name_from_manifest(cls, app_dir: str):
        """Retrieves the application name assuming there is a manifest.json file

        Arguments:
            app_dir: Path to the gzipped application. In this same directory
                     there should be a manifest.json file

        Returns:
            The application name
        """
        manifest_path = os.path.join(os.path.dirname(app_dir), cls.MANIFEST_NAME)
        with open(manifest_path, 'r') as file:
            manifest = json.loads(file.read())
        return manifest['name']

    def _refresh(self):
        """ Updates the state of the application. If the application is not present, assertion kicks in """
        apps = self.get_list()
        app = next((a for a in apps if a.name == self.name), None)
        assert app is not None, "Cannot find application {}".format(self.name)
        for attr_name in self._REFRESH_ATTRIBUTES:
            new_value = getattr(app, attr_name)
            setattr(self, attr_name, new_value)

    @retry(AssertionError, tries=30, delay=2)
    def _ensure_has_id(self):
        """ Waits for the application to receive an id. If no id is found, assertion is raised """
        self._refresh()
        assert self.id != "", "App {} hasn't received id in 60s. State: {}".format(self.name, format(self._state))
