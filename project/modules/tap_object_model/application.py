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
from modules import test_names
from ._api_model_superclass import ApiModelSuperclass
from ._tap_object_superclass import TapObjectSuperclass


class Application(ApiModelSuperclass, TapObjectSuperclass):
    """ Application represents an Application on TAP.
    It allows to push, delete, retrieve TAP applications using 'console' or 'api-service' REST APIs.
    It enables sending http requests to such applications.
    """

    # id is the application instance id, app_id is the application id
    _COMPARABLE_ATTRIBUTES = ["name", "id", "app_id", "image_type", "state",
                              "replication", "running_instances", "urls"]
    _REFRESH_ATTRIBUTES = ["id", "image_type", "state", "replication",
                           "running_instances", "urls"]

    MANIFEST_NAME = "manifest.json"
    RUN_SH_NAME = "run.sh"

    def __init__(self, app_id: str, app_inst_id: str, name: str, bindings: list,
                 image_type: str, state: str, replication: int, running_instances: int,
                 urls: list, client: HttpClient=None):
        """Class initializer.

        Args:
            app_id: Id of the application
            app_inst_id: Id of instance of the application
            name: Name of the application
            bindings: List of services that application is binded to
            image_type: Defines the image type
            state: Current state of the application
            replication: Amount of replications
            running_instances: Amount of running instances
            urls: Urls that the application used
            client: The Http client to use.
        """
        super().__init__(object_id=app_inst_id, client=client)
        self.app_id = app_id
        self.name = name
        self.bindings = bindings
        self.image_type = image_type
        self.state = state
        self.replication = replication
        self.running_instances = running_instances
        self.urls = tuple(urls)
        self._request_session = requests.session()

    def __repr__(self):
        return "{} (name={}, app_id={}, app_inst_id={})".format(self.__class__.__name__,
                                                                self.name,
                                                                self.app_id,
                                                                self.id)

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
    def save_manifest(cls, *, app_path, name, instances, app_type, bindings):
        """
        Fill manifest with parameters, save as file in application directory.
        Return path to the manifest file.
        """
        manifest = {
            "name": name,
            "instances": instances,
            "type": app_type,
            "bindings": bindings
        }
        if os.path.isfile(app_path):
            manifest_dir = os.path.dirname(app_path)
        else:
            manifest_dir = app_path
        manifest_path = os.path.join(manifest_dir, cls.MANIFEST_NAME)
        with open(manifest_path, "w") as f:
            f.write(json.dumps(manifest))
        return manifest_path

    @classmethod
    def set_run_sh_access(cls, *, app_path):
        if os.path.isfile(app_path):
            run_sh_dir = os.path.dirname(app_path)
        else:
            run_sh_dir = app_path

        run_sh_path = os.path.join(run_sh_dir, cls.RUN_SH_NAME)
        if os.path.isfile(run_sh_path):
            os.chmod(run_sh_path, 0o777)

    @classmethod
    def push(cls, context, *, app_path: str, tap_cli: TapCli, app_type: str,
             name: str=None, instances: int=1, client: HttpClient=None,
             bindings: list=None):
        """Pushes the application from source directory with provided name,
        services and envs.

        After pushing the application, method verfies that the application was
        pushed. If not, exceptions is raised.
        It waits for the applications instance id to appear. If the instance id
        does not appear, assertion is raised.

        Args:
            context: context object that will store created applications. It is used
                     later to perform a cleanup.
            app_path: path to the application archive or to the application directory
            tap_cli: tap client, that will be used to push the app.
            app_type: "type" parameter in manifest.json
            name: "name" parameter in manifest.json, if None, will be auto-generated
            instances: "instances" parameter in manifest.json
            client: The Http client to use. If None, default (admin via console)
                    will be used. It will be used to verify if the app was pushed
            bindings: List of services bindings that the application will use

            Returns:
                Application class instance
        """
        if name is None:
            name = test_names.generate_test_object_name(separator="")
        cls.save_manifest(app_path=app_path, name=name, instances=instances, app_type=app_type, bindings=bindings)
        cls.set_run_sh_access(app_path=app_path)
        tap_cli.login()
        try:
            tap_cli.push(app_path=app_path)
        except Exception as exc:
            # If the application already exists, than don't remove it (as this
            # will break later tests), just raise the error
            if "application with name: " + name + " already exists!" in str(exc):
                raise

            apps = Application.get_list(client=client)
            application = next((app for app in apps if app.name == name), None)
            if application is not None:
                application.cleanup()
            raise

        # Find the application and return it
        apps = Application.get_list(client=client)
        app = next((a for a in apps if a.name == name), None)
        assert app is not None, "App {} has not been created on the platform".format(name)

        # Wait for the application to receive the application instance id
        app._ensure_has_id(client=client)
        context.test_objects.append(app)
        return app

    @property
    def is_stopped(self) -> bool:
        """Returns True if application is stopped."""
        return self.state.upper() == TapEntityState.STOPPED

    @property
    def is_running(self) -> bool:
        """Returns True if any of the application instances are running."""
        return self.state == TapEntityState.RUNNING

    @classmethod
    def get(cls, app_inst_id: str, client: HttpClient=None):
        """Retrieves the application based on app instance id

        Args:
            app_inst_id: id of the application instance to retrieve

        Returns:
            The application
        """
        if client is None:
            client = cls._get_default_client()
        response = api.get_application(app_id=app_inst_id, client=client)
        return cls._from_response(response, client)

    @classmethod
    def get_list(cls, client: HttpClient=None):
        """Get list of applications from Console / service-catalog API

        Args:
            client: Http client to use
        """
        if client is None:
            client = cls._get_default_client()
        response = api.get_applications(client=client)
        return cls._list_from_response(response, client)

    def delete(self, client: HttpClient=None):
        """ Deletes the application from TAP """
        api.delete_application(client=self._get_client(client),
                               app_id=self.id)

    def start(self, client: HttpClient=None):
        """ Sends the start command to application """
        api.start_application(app_id=self.id, client=self._get_client(client))

    def stop(self, client: HttpClient=None):
        """ Sends the stop command to application """
        api.stop_application(app_id=self.id, client=self._get_client(client))

    def restart(self, client: HttpClient=None):
        """Sends the restart command to application """
        api.restart_application(app_id=self.id, client=self._get_client(client))

    def get_logs(self, client: HttpClient=None):
        return api.get_application_logs(app_id=self.id, client=self._get_client(client))

    def scale(self, *, replicas: int, client: HttpClient=None):
        return api.scale_application(app_id=self.id, replicas=replicas, client=self._get_client(client))

    @retry(AssertionError, tries=15, delay=3)
    def ensure_responding(self, *, path=''):
        response = self.api_request(path=path)
        assert response is not None, "App {} is not responding.".format(self.name)

    @retry(AssertionError, tries=30, delay=2)
    def ensure_running(self, client: HttpClient=None):
        """Waits for the application to start for a given number of tries.

        If the application hasn't started, assertion kicks in
        """
        self._refresh(client=client)
        assert self.is_running is True, "App {} is not started. App state: {}".format(self.name, self.state)

    @retry(AssertionError, tries=30, delay=2)
    def ensure_stopped(self, client: HttpClient=None):
        """Waits for the application to stop for a given number of tries.

        If the application hasn't stopped, assertion kicks in
        """
        self._refresh(client=client)
        assert self.is_stopped is True, "App {} is not stopped. App state: {}".format(self.name, self.state)

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
        """Creates an Application object based on the response

        Args:
            response: Response from api
            client: HttpClient that created Application will use

        Returns:
            Application object created from response
        """
        return cls(app_id=response.get("classId", ""), app_inst_id=response.get("id", ""),
                   name=response["name"], bindings=response["bindings"],
                   image_type=response["imageType"], state=response["state"],
                   replication=response["replication"], running_instances=response["running_instances"],
                   urls=response["urls"], client=client)

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

    def _refresh(self, client: HttpClient=None):
        """ Updates the state of the application. If the application is not present,
        assertion kicks in.

        Args:
            client: HttpClient to use
        """
        apps = self.get_list(client=self._get_client(client))
        app = next((a for a in apps if a.name == self.name), None)
        assert app is not None, "Cannot find application {}".format(self.name)
        for attr_name in self._REFRESH_ATTRIBUTES:
            new_value = getattr(app, attr_name)
            setattr(self, attr_name, new_value)

    @retry(AssertionError, tries=30, delay=2)
    def _ensure_has_id(self, client: HttpClient=None):
        """ Waits for the application to receive an id. If no id is found,
        assertion is raised.

        Args:
            client: HttpClient to use
        """
        self._refresh(client=client)
        assert self.id != "", "App {} hasn't received id yet. State: {}".format(self.name, format(self.state))
