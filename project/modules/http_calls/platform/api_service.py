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

from modules.constants import HttpStatus
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.http_client import HttpClient
from modules.http_client.configuration_provider.k8s_service import ServiceConfigurationProvider


def _get_client():
    configuration = ServiceConfigurationProvider.get()
    return HttpClientFactory.get(configuration)


def post(path):
    """ POST /{path} """
    response = _get_client().request(HttpMethod.POST,
                                     path=path,
                                     raw_response=True,
                                     msg="API-SERVICE: post /{}".format(path))
    return response


def put(path, body={}):
    """ PUT /{path} """
    response = _get_client().request(HttpMethod.PUT,
                                     path=path,
                                     body=body,
                                     raw_response=True,
                                     msg="API-SERVICE: put /{}".format(path))
    return response


def push_application(file_path, manifest_path):
    """ POST /applications """
    files = {"blob": (file_path, open(file_path, 'rb'), "multipart/form-data"),
             "manifest": (manifest_path, open(manifest_path, 'rb'), "multipart/form-data")}

    response = _get_client().request(HttpMethod.POST,
                                     path="applications",
                                     files=files,
                                     raw_response=True,
                                     msg="API-SERVICE: push application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response


def get_applications(org_id: str=None, client: HttpClient=None):
    """Retrieves list of applications using REST call
    GET /applications

    Args:
        client: HttpClient to use
        org_id: Optional organization id

    Returns:
        Response containing list of apps.
    """
    if client is None:
        client = _get_client()

    query_params = {}
    path = "applications"
    if org_id is not None:
        query_params["org_id"] = org_id

    response = client.request(HttpMethod.GET,
                              path=path,
                              params=query_params,
                              raw_response=True,
                              msg="Get application list")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def get_application(app_id: str, client: HttpClient=None):
    """Retrieves the application details using REST call
    GET /applications/{app_id}

    Args:
        client: Http client to use
        app_id: Id of the application

    Returns:
        Raw response to the call
    """
    if client is None:
        client = _get_client()

    path = "applications/{}".format(app_id)
    response = client.request(HttpMethod.GET,
                              path=path,
                              raw_response=True,
                              msg="Get application details")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def get_application_logs(app_id: str, client: HttpClient=None):
    """Attempts to retrieve application logs using REST call
    GET /logs/{app_id}

    Args:
        client: Http client to use
        app_id: Id of the application

    Returns:
        Raw response to the call
    """
    if client is None:
        client = _get_client()

    path = "logs/{}".format(app_id)
    response = client.request(HttpMethod.GET,
                              path=path,
                              raw_response=True,
                              msg="Get application logs")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def delete_application(app_id: str, client: HttpClient=None):
    """Deletes an application with provided id using REST call
    DELETE /applications/{app_id}

    Args:
        client: HttpClient to use
        app_id: Id of the application

    Returns:
        Raw response of the operation
    """
    if client is None:
        client = _get_client()

    response = client.request(HttpMethod.DELETE,
                              path="applications/{}".format(app_id),
                              msg="Delete application")
    return response


def scale_application(id, replicas):
    """ PUT /applications/{id}/scale """
    body = {"replicas": replicas}
    path = "applications/{}/scale".format(id)
    response = put(path, body)
    return response


def start_application(app_id: str, client: HttpClient=None):
    """Attempts to start application with a provided client using REST call
    PUT applications/{app_id}/start

    Args:
        client: Http client to use
        app_id: Id of application to start

    Returns:
        Raw response to the request
    """
    if client is None:
        client = _get_client()

    path = "applications/{}/start".format(app_id)
    response = client.request(HttpMethod.PUT,
                              path=path,
                              raw_response=True,
                              msg="Start application")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def stop_application(app_id: str, client: HttpClient=None):
    """Attempts to stop application with a provided client using REST call
    PUT applications/{app_id}/stop

    Args:
        client: Http client to use
        app_id: Id of application to stop

    Returns:
        Raw response to the request
    """
    if client is None:
        client = _get_client()

    path = "applications/{}/stop".format(app_id)
    response = client.request(HttpMethod.PUT,
                              path=path,
                              raw_response=True,
                              msg="Stop application")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def get_catalog(client: HttpClient):
    """ GET /catalog """
    return client.request(HttpMethod.GET, path="catalog")


def get_offering(client: HttpClient, offering_id):
    """ GET /catalog/:offering_id """
    return client.request(HttpMethod.GET, path="catalog/{}".format(offering_id))


def create_offering(client: HttpClient, template_body: dict, service_name: str, description: str, bindable: bool,
                    tags: list, plans: list):
    """ POST /offering """
    body = {
        "template": {
            "body": template_body,
            "hooks": None
        },
        "services": [{
            "name": service_name,
            "description": description,
            "bindable": bindable,
            "tags": tags,
            "plans": plans,
            "metadata": []
        }]
    }
    response = client.request(HttpMethod.POST, path="offering", body=body, raw_response=True)
    assert response.status_code == HttpStatus.CODE_CREATED
    return response.json()


def delete_offering(client: HttpClient, offering_id):
    """ DELETE /catalog/:offering_id """
    # TODO verify path, endpoint not documented
    response = client.request(HttpMethod.DELETE, path="catalog/{}".format(offering_id), raw_response=True)
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def get_app_bindings(app_guid, client=None):
    """GET /bindings/{app_guid}"""
    if client is None:
        client = _get_client()
    response = client.request(
        method=HttpMethod.GET,
        path="bindings/{}".format(app_guid),
        msg="Get application bindings"
    )
    return response["resources"]


def bind(service_instance_guid, app_guid, client=None):
    """POST /bind/{service_instance_guid}/{app_guid}"""
    if client is None:
        client = _get_client()
    return client.request(
        method=HttpMethod.POST,
        path="bind/{}/{}".format(service_instance_guid, app_guid),
        msg="Bind app and instance"
    )


def unbind(service_instance_guid, app_guid, client=None):
    """POST /unbind/{app_guid}/{service_instance_guid}"""
    if client is None:
        client = _get_client()
    return client.request(
        method=HttpMethod.POST,
        path="unbind/{}/{}".format(app_guid, service_instance_guid),
        msg="Unbind app from instance"
    )
