#
# Copyright (c) 2017 Intel Corporation
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
from urllib.parse import urlparse

import requests
from requests import exceptions
from retry import retry

import config
from modules.constants import TapEntityState
from modules.exceptions import UnexpectedResponseError
import modules.http_calls.platform.api_service as api
from modules.http_client import HttpClient
from modules.tap_logger import log_http_request, log_http_response
from ._api_model_superclass import ApiModelSuperclass
from ._tap_object_superclass import TapObjectSuperclass


class Application(ApiModelSuperclass, TapObjectSuperclass):
    """ Application represents an Application on TAP.
    It allows to push, delete, retrieve TAP applications using 'console' or 'api-service' REST APIs.
    It enables sending http requests to such applications.
    """

    # id is the application instance id, app_id is the application id
    _COMPARABLE_ATTRIBUTES = ["name", "id", "image_type", "state",
                              "replication", "running_instances", "urls"]
    _REFRESH_ATTRIBUTES = ["id", "image_type", "state", "replication",
                           "running_instances", "urls"]

    RUN_SH_NAME = "run.sh"

    def __init__(self, app_id: str, name: str, bindings: list,
                 image_type: str, state: str, replication: int, running_instances: int,
                 urls: list, client: HttpClient=None):
        """Class initializer.

        Args:
            app_id: Id of the application
            name: Name of the application
            bindings: List of services that application is binded to
            image_type: Defines the image type
            state: Current state of the application
            replication: Amount of replications
            running_instances: Amount of running instances
            urls: Urls that the application used
            client: The Http client to use.
        """
        super().__init__(object_id=app_id, client=client)
        self.name = name
        self.bindings = bindings
        self.image_type = image_type
        self.state = state
        self.replication = replication
        self.running_instances = running_instances
        self.urls = tuple(urls)
        self._request_session = requests.session()
        self._request_session.verify = config.ssl_validation
        self._is_deleted = False

    def __repr__(self):
        return "{} (name={}, app_id={})".format(self.__class__.__name__,
                                                self.name,
                                                self.id)

    @classmethod
    def push(cls, context, *, app_path: str, name: str, manifest_path: str = None,
             manifest: dict = None, client: HttpClient=None):
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
            name: Name of the application
            manifest_path: path to the manifest file
            manifest: manifest file content (used only if manifest_path is None)
            client: The Http client to use. If None, default (admin via console)
                    will be used. It will be used to verify if the app was pushed

            Returns:
                Application class instance
        """
        if client is None:
            client = cls._get_default_client()
        try:
            if manifest_path:
                api.create_application_with_manifest_path(client=client, file_path=app_path,
                                                          manifest_path=manifest_path)
            elif manifest:
                api.create_application_with_manifest(client=client, file_path=app_path,
                                                     manifest=manifest)
            else:
                raise ValueError('Neither manifest_path nor manifest is passed')
        except UnexpectedResponseError as exc:
            # If the application already exists, than don't remove it (as this
            # will break later tests), just raise the error
            if exc.status == 409:
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
    def get_by_name(cls, name: str, client: HttpClient = None):
        """Retrieves the application id based on app name

        Args:
            name: name of the application instance to retrieve

        Returns:
            The application
        """
        if client is None:
            client = cls._get_default_client()
        for application in api.get_applications(client=client):
            if application['name'] == name:
                return cls._from_response(application, client)

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
        if self._is_deleted is True:
            return

        try:
            api.delete_application(client=self._get_client(client),
                                   app_id=self.id)
            self._set_deleted(True)
        except UnexpectedResponseError:
            raise

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

    def bind(self, *, service_instance_id, client: HttpClient=None):
        return api.bind_svc(client=self._get_client(client), app_id=self.id, service_instance_id=service_instance_id)

    def unbind(self, *, service_instance_id, client: HttpClient=None):
        return api.unbind_svc(client=self._get_client(client), app_id=self.id, service_instance_id=service_instance_id)

    def get_bindings(self, client: HttpClient=None):
        return api.get_app_bindings(client=self._get_client(client), app_id=self.id)

    @retry(AssertionError, tries=10, delay=2)
    def ensure_bound(self, service_instance_id, client: HttpClient=None):
        bindings = self.get_bindings(client=client)
        assert bindings is not None
        ids = next((e["entity"]["service_instance_guid"] for e in bindings), None)
        assert service_instance_id in ids

    @retry(AssertionError, tries=10, delay=2)
    def ensure_unbound(self, service_instance_id, client: HttpClient = None):
        bindings = self.get_bindings(client=client)
        if bindings is not None:
            ids = next((e["entity"]["service_instance_guid"] for e in bindings), None)
            assert service_instance_id not in ids
        else:
            assert bindings is None

    @retry(AssertionError, tries=15, delay=3)
    def ensure_responding(self, *, path=''):
        response = self.api_request(path=path)
        assert response is not None, "App {} is not responding.".format(self.name)

    @retry(AssertionError, tries=150, delay=2)
    def ensure_running(self, client: HttpClient=None):
        """Waits for the application to start for a given number of tries.

        If the application hasn't started, assertion kicks in
        """
        self._refresh(client=client)
        if self.state == TapEntityState.FAILURE:
            raise ValueError("Application is in FAILURE, aborting retrying")
        assert self.is_running is True, "App {} is not started. App state: {}".format(self.name, self.state)

    @retry(AssertionError, tries=30, delay=2)
    def ensure_stopped(self, client: HttpClient=None):
        """Waits for the application to stop for a given number of tries.

        If the application hasn't stopped, assertion kicks in
        """
        self._refresh(client=client)
        if self.state == TapEntityState.FAILURE:
            raise ValueError("Application is in FAILURE, aborting retrying")
        assert self.is_stopped is True, "App {} is not stopped. App state: {}".format(self.name, self.state)

    def api_request(self, path: str, method: str="GET", scheme: str=config.external_protocol, hostname: str=None, data: dict=None,
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
        hostname = self._set_scheme(url=hostname, scheme=scheme)
        request = self._request_session.prepare_request(requests.Request(
            method=method.upper(),
            url="{}/{}".format(hostname, path),
            params=params,
            data=data,
            json=body
        ))
        log_http_request(request, "")
        response = self._send_request(request)
        log_http_response(response)
        if raw is True:
            return response
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @retry(exceptions=requests.exceptions.ConnectionError, tries=2)
    def _send_request(self, request):
        return self._request_session.send(request)

    @classmethod
    def _set_scheme(cls, *, url: str, scheme: str="http"):
        """Checks if url has scheme.
        If not - adds specified scheme (http by default),
        else - replaces scheme with specified.

        Args:
            url: App url
            scheme: Url scheme e.g. http, https

        Returns:
            Application url with scheme (default value is http)
        """
        url = urlparse(url)
        if (url.scheme or url.netloc) == '':
            return "{}://{}".format(scheme, url.geturl())
        else:
            url = url._replace(scheme=scheme)
            return url.geturl()

    @classmethod
    def _from_response(cls, response: dict, client: HttpClient):
        """Creates an Application object based on the response

        Args:
            response: Response from api
            client: HttpClient that created Application will use

        Returns:
            Application object created from response
        """
        return cls(app_id=response.get("id", ""), name=response["name"],
                   bindings=response["bindings"], image_type=response["imageType"],
                   state=response["state"], replication=response["replication"],
                   running_instances=response["running_instances"],
                   urls=response["urls"], client=client)

    def _refresh(self, client: HttpClient=None):
        """ Updates the state of the application. If the application is not present,
        assertion kicks in.

        Args:
            client: HttpClient to use
        """
        app = self.get(app_inst_id=self.id, client=self._get_client(client))
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

    def cleanup(self, client: HttpClient=None):
        if client is None:
            client = self._get_default_client()
        self._refresh(client=client)
        if self.state == TapEntityState.RUNNING:
            self.stop()
            self.ensure_stopped()
        self.delete()

    @classmethod
    def get_image(cls, app_inst_id: str, client: HttpClient = None):
        get_sample_python_app = api.get_application(client=client, app_id=app_inst_id)
        metadata = get_sample_python_app['metadata']
        image = ''
        for key in metadata:
            if 'APPLICATION_IMAGE_ADDRESS' in key['key']:
                image = key['value']
        return image
