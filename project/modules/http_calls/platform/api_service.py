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


# --------------------------------------- offerings --------------------------------------- #


def get_catalog(*, client: HttpClient):
    """ GET /catalog """
    # TODO will be changed to GET /offerings
    if client is None:
        client = _get_client()
    return client.request(HttpMethod.GET, path="catalog")


def get_offerings(*, client: HttpClient=None):
    """ GET /offerings """
    if client is None:
        client = _get_client()
    return client.request(HttpMethod.GET, path="offerings")


def create_offering(*, client: HttpClient, template_body: dict, service_name: str, description: str, bindable: bool,
                    tags: list, plans: list):
    """ POST /offerings """
    # TODO will be changed to POST /offerings
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
    if client is None:
        client = _get_client()
    response = client.request(HttpMethod.POST, path="offerings", body=body, raw_response=True)
    assert response.status_code == HttpStatus.CODE_CREATED
    # TODO should return response.json()
    return response.json()


def get_offering(*, client: HttpClient, offering_id):
    """ GET /catalog/{offering_id} """
    # TODO will be changed to GET /offerings/{offering_id}
    if client is None:
        client = _get_client()
    return client.request(HttpMethod.GET, path="catalog/{}".format(offering_id))


def delete_offering(*, client: HttpClient, offering_id):
    """ DELETE /catalog/{offering_id} """
    # TODO will be changed to GET /offerings/{offering_id}
    if client is None:
        client = _get_client()
    response = client.request(HttpMethod.DELETE, path="catalog/{}".format(offering_id), raw_response=True)
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    # TODO should return response.json()
    return response.json()


# --------------------------------------- applications --------------------------------------- #


def create_application(*, file_path, manifest_path):
    """ POST /applications """
    files = {
        "blob": (file_path, open(file_path, 'rb'), "multipart/form-data"),
        "manifest": (manifest_path, open(manifest_path, 'rb'), "multipart/form-data")
    }
    response = _get_client().request(HttpMethod.POST, path="applications", files=files, raw_response=True,
                                     msg="Create an application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    # TODO should return response.json()
    return response


def get_applications(*, org_id: str=None, client: HttpClient=None):
    """ GET /applications

    Args:
        client: HttpClient to use
        org_id: Optional organization id

    Returns:
        Response containing list of apps.
    """
    if client is None:
        client = _get_client()

    query_params = {}
    if org_id is not None:
        query_params["org_id"] = org_id

    response = client.request(HttpMethod.GET, path="applications", params=query_params, raw_response=True,
                              msg="List applications")
    assert response.status_code == HttpStatus.CODE_OK
    # TODO should return response.json()
    return response


def get_application(*, app_id: str, client: HttpClient=None):
    """ GET /applications/{app_id}

    Args:
        client: Http client to use
        app_id: Id of the application

    Returns:
        Raw response to the call
    """
    if client is None:
        client = _get_client()
    response = client.request(HttpMethod.GET, path="applications/{}".format(app_id), raw_response=True,
                              msg="Get application")
    assert response.status_code == HttpStatus.CODE_OK
    # TODO should return response.json()
    return response


def delete_application(*, app_id: str, client: HttpClient=None):
    """ DELETE /applications/{app_id}

    Args:
        client: HttpClient to use
        app_id: Id of the application

    Returns:
        Raw response of the operation
    """
    if client is None:
        client = _get_client()
    return client.request(HttpMethod.DELETE, path="applications/{}".format(app_id), msg="Delete application")


def get_application_logs(*, app_id: str, client: HttpClient=None):
    # TODO will be changed to GET /applications/{app_id}/logs
    """ GET /logs/{app_id}

    Args:
        client: Http client to use
        app_id: Id of the application

    Returns:
        Raw response to the call
    """
    if client is None:
        client = _get_client()
    response = client.request(HttpMethod.GET, path="logs/{}".format(app_id), raw_response=True,
                              msg="Get application logs")
    assert response.status_code == HttpStatus.CODE_OK
    # TODO should return response.json()
    return response


def scale_application(*, app_id, replicas):
    # TODO will be changed to PUT /applications/{app_id}/scale
    """ PUT /applications/{id}/scale """
    response = _get_client().request(HttpMethod.PUT, path="applications/{}/scale".format(id),
                                     body={"replicas": replicas}, raw_response=True, msg="Scale application")
    # TODO should return response.json()
    return response


def get_app_bindings(*, app_id, client=None):
    # TODO will be changed to GET /applications/{app_id}/bindings
    """ GET /bindings/{app_guid}"""
    if client is None:
        client = _get_client()
    response = client.request(
        method=HttpMethod.GET,
        path="bindings/{}".format(app_id),
        msg="Get application bindings"
    )
    return response["resources"]


def bind(*, service_instance_guid, app_id, client=None):
    """ POST /bind/{service_instance_guid}/{app_guid} """
    # TODO will be changed to POST /applications/{app_id}/bindings
    if client is None:
        client = _get_client()
    return client.request(method=HttpMethod.POST, path="bind/{}/{}".format(service_instance_guid, app_id),
                          msg="Bind app and instance")


def unbind(*, service_instance_guid, app_id, client=None):
    """ POST /unbind/{app_guid}/{service_instance_guid} """
    # TODO will be changed to DELETE /applications/{app_id}/bindings
    if client is None:
        client = _get_client()
    return client.request(method=HttpMethod.POST, path="unbind/{}/{}".format(app_id, service_instance_guid),
                          msg="Unbind app from instance")


def start_application(*, app_id: str, client: HttpClient=None):
    """ PUT applications/{app_id}/start

    Args:
        client: Http client to use
        app_id: Id of application to start

    Returns:
        Raw response to the request
    """
    if client is None:
        client = _get_client()
    response = client.request(HttpMethod.PUT, path="applications/{}/start".format(app_id), raw_response=True,
                              msg="Start application")
    assert response.status_code == HttpStatus.CODE_OK
    # TODO should return response.json()
    return response


def stop_application(*, app_id: str, client: HttpClient=None):
    """ PUT applications/{app_id}/stop

    Args:
        client: Http client to use
        app_id: Id of application to stop

    Returns:
        Raw response to the request
    """
    if client is None:
        client = _get_client()
    response = client.request(HttpMethod.PUT, path="applications/{}/stop".format(app_id), raw_response=True,
                              msg="Stop application")
    assert response.status_code == HttpStatus.CODE_OK
    # TODO should return response.json()
    return response


# --------------------------------------- services --------------------------------------- #


def get_services(*, name=None, offering_id=None, plan_name=None, limit=None, skip=None, client=None):
    """ GET /services """
    query_params = {
        "offering_id": offering_id,
        "plan_name": plan_name,
        "name": name,
        "limit": limit,
        "skip": skip
    }
    query_params = {k: v for k, v in query_params.items() if v is not None}
    if client is None:
        client = _get_client()
    return client.request(method=HttpMethod.GET, path="services", params=query_params, msg="List service instances")


def create_service(*, name, service_plan_id, offering_id, params, client=None):
    """POST /services/{offering_id}"""
    # TODO will be changed to POST /services, with offering_id passed as "classId" in body
    metadata = [{"key": "PLAN_ID", "value": service_plan_id}]
    if params is not None:
        metadata = metadata + [{"key": key, "value": val} for key, val in params.items()]
    body = {
        "metadata": metadata,
        "name": name,
        "type": "SERVICE"
    }
    if client is None:
        client = _get_client()
    return client.request(method=HttpMethod.POST, path="services/{}".format(offering_id), body=body,
                          msg="Create service instance")


def get_service(*, service_id, client=None):
    """ GET /services/{service_id} """
    if client is None:
        client = _get_client()
    return client.request(method=HttpMethod.GET, path="services/{}".format(service_id), msg="Get service instance")


def delete_service(*, service_id, client):
    """ DELETE /services/{service_id} """
    if client is None:
        client = _get_client()
    return client.request(method=HttpMethod.DELETE, path="services/{}".format(service_id),
                          msg="Delete service instance")
