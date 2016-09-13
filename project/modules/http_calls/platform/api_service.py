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
from modules.http_client.configuration_provider.k8s_service import ApiServiceConfigurationProvider


def _get_client():
    configuration = ApiServiceConfigurationProvider.get()
    return HttpClientFactory.get(configuration)


def get(path):
    """ GET /{path} """
    response = _get_client().request(HttpMethod.GET,
                                     path=path,
                                     raw_response=True,
                                     msg="API-SERVICE: get /{}".format(path))
    assert response.status_code == HttpStatus.CODE_OK
    return response


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
                                     msg="API-SERVICE: put /{}".format(path))
    return response


def push_application(file_path, manifest_path):
    """ POST /applications """
    files = {"blob": (file_path, open(file_path, 'rb'), "multipart/form-data"),
             "manifest": (manifest_path, open(manifest_path, 'rb'), "multipart/form-data")}

    response = _get_client().request(HttpMethod.POST,
                                     path="applications",
                                     files=files,
                                     msg="API-SERVICE: push application")
    assert response.status_code == HttpStatus.CODE_CREATED
    return response


def get_applications(client: HttpClient, org_id: str=None):
    """Retrieves list of applications using REST call
    GET /applications

    Args:
        client: HttpClient to use
        org_id: Optional organization id

    Returns:
        Response containing list of apps.
    """
    query_params = {}
    path = "applications"
    if org_id is not None:
        query_params["org_id"] = org_id

    response = _get_client().request(HttpMethod.GET,
                                     path=path,
                                     params=query_params,
                                     raw_response=True,
                                     msg="Get application list")
    assert response.status_code == HttpStatus.CODE_OK
    return response




def get_application(id):
    """ GET /applications/{id} """
    response = get("applications/{}".format(id))
    return response


def get_application_logs(id):
    """ GET /logs/{id} """
    response = get("logs/{}".format(id))
    return response


def delete_application(client: HttpClient, app_id: str):
    """Deletes an application with provided id using REST call
    DELETE /applications/{app_id}

    Args:
        client: HttpClient to use
        app_id: Id of the application

    Returns:
        Raw response of the apperation
    """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="applications/{}".format(app_id),
                                     msg="Delete application")
    return response


def scale_application(id, replicas):
    """ PUT /applications/{id}/scale """
    body = {"replicas": replicas}
    path = "applications/{}/scale".format(id)
    response = put(path, body)
    return response


def start_application(id):
    """ PUT /applications/{id}/start """
    path = "applications/{}/start".format(id)
    response = put(path)
    return response


def stop_application(id):
    """ PUT /applications/{id}/stop """
    path = "applications/{}/stop".format(id)
    response = put(path)
    return response
