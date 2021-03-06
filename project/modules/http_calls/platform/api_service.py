#
# Copyright (c) 2016-2017 Intel Corporation
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
from io import StringIO

from modules.constants import HttpStatus
from modules.http_client import HttpMethod
from modules.http_client.http_client import HttpClient

"""
This module implements api-service HTTP methods.
Most of them are shared also by console.
"""


# --------------------------------------- offerings --------------------------------------- #


def get_offerings(*, client: HttpClient) -> list:
    """ GET /offerings """
    return client.request(HttpMethod.GET, path="offerings", msg="List offerings in marketplace")


def create_offering(*, client: HttpClient, template_body: dict, service_name: str, description: str, bindable: bool,
                    tags: list, plans: list):
    """ POST /offerings """
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
    response = client.request(HttpMethod.POST, path="offerings", body=body, raw_response=True)
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def create_offering_from_binary(*, jar_path: str, manifest_path: str, offering_path, client: HttpClient):
    """ POST /offerings/binary """
    files = {
        "blob": (jar_path, open(jar_path, 'rb'), "multipart/form-data"),
        "manifest": (manifest_path, open(manifest_path, 'rb'), "multipart/form-data"),
        "offering": (offering_path, open(offering_path, 'rb'), "multipart/form-data"),
    }
    response = client.request(HttpMethod.POST, path="offerings/binary", files=files, raw_response=True,
                              msg="Create an offering")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def get_offering(*, client: HttpClient, offering_id: str):
    """ GET /offerings/{offering_id} """
    return client.request(HttpMethod.GET,
                          path="offerings/{offering_id}",
                          path_params={'offering_id': offering_id})


def delete_offering(*, client: HttpClient, offering_id):
    """ DELETE /offerings/{offering_id} """
    response = client.request(HttpMethod.DELETE,
                              path="offerings/{offering_id}",
                              path_params={'offering_id': offering_id},
                              raw_response=True)
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


# --------------------------------------- applications --------------------------------------- #


def create_application_with_manifest_path(*, client: HttpClient, file_path: str, manifest_path: str):
    """ POST /applications """
    files = {
        "blob": (file_path, open(file_path, 'rb'), "multipart/form-data"),
        "manifest": (manifest_path, open(manifest_path, 'rb'), "multipart/form-data")
    }
    response = client.request(HttpMethod.POST, path="applications", files=files, raw_response=True,
                              msg="Create an application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def create_application_with_manifest(*, client: HttpClient, file_path: str, manifest: dict):
    """ POST /applications """
    manifest_str = json.dumps(manifest)
    files = {
        "blob": (file_path, open(file_path, 'rb'), "multipart/form-data"),
        "manifest": (file_path, StringIO(manifest_str), "multipart/form-data")
    }
    response = client.request(HttpMethod.POST, path="applications", files=files, raw_response=True,
                              msg="Create an application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def get_applications(*, client: HttpClient, org_id: str=None):
    """ GET /applications """
    query_params = {}
    if org_id is not None:
        query_params["org_id"] = org_id

    response = client.request(HttpMethod.GET, path="applications", params=query_params, raw_response=True,
                              msg="List applications")
    assert response.status_code == HttpStatus.CODE_OK
    return response.json()


def get_application(*, client: HttpClient, app_id: str):
    """ GET /applications/{app_id} """
    response = client.request(HttpMethod.GET,
                              path="applications/{app_id}",
                              path_params={'app_id': app_id},
                              raw_response=True,
                              msg="Get application")
    assert response.status_code == HttpStatus.CODE_OK
    return response.json()


def delete_application(*, client: HttpClient, app_id: str):
    """ DELETE /applications/{app_id} """
    response = client.request(HttpMethod.DELETE,
                              path="applications/{app_id}",
                              path_params={'app_id': app_id},
                              msg="Delete application",
                              raw_response=True)
    assert response.status_code == HttpStatus.CODE_NO_CONTENT


def get_application_logs(*, client: HttpClient, app_id: str):
    """ GET /applications/{app_id}/logs """
    response = client.request(HttpMethod.GET,
                              path="applications/{app_id}/logs",
                              path_params={'app_id': app_id},
                              raw_response=True,
                              msg="Get application logs")
    assert response.status_code == HttpStatus.CODE_OK
    return response.json()


def scale_application(*, client: HttpClient, app_id: str, replicas):
    """ PUT /applications/{app_id}/scale """
    body = {
        "replicas": replicas
    }
    response = client.request(HttpMethod.PUT,
                              path="applications/{app_id}/scale",
                              path_params={'app_id': app_id},
                              body=body,
                              raw_response=True,
                              msg="Scale application")
    return response.json()


def start_application(*, client: HttpClient, app_id: str):
    """ PUT /applications/{app_id}/start """
    response = client.request(HttpMethod.PUT,
                              path="applications/{app_id}/start",
                              path_params={'app_id': app_id},
                              raw_response=True,
                              msg="Start application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def stop_application(*, client: HttpClient, app_id: str):
    """ PUT /applications/{app_id}/stop """
    response = client.request(HttpMethod.PUT,
                              path="applications/{app_id}/stop",
                              path_params={'app_id': app_id},
                              raw_response=True,
                              msg="Stop application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def restart_application(*, client: HttpClient, app_id: str):
    """ PUT /applications/{app_id}/restart """
    response = client.request(HttpMethod.PUT,
                              path="applications/{app_id}/restart",
                              path_params={'app_id': app_id},
                              raw_response=True,
                              msg="Restart application")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()

def start_service(*, client: HttpClient, srv_id: str):
    """ PUT /services/{srv_id}/start
    Attempts to start service instance

    Args:
        client: HttpClient to use
        srv_id: id of the service instance to start
    """
    response = client.request(HttpMethod.PUT,
                              path="services/{srv_id}/start",
                              path_params={'srv_id': srv_id},
                              raw_response=True,
                              msg="Start service instance")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def stop_service(*, client: HttpClient, srv_id: str):
    """ PUT /services/{srv_id}/stop
    Attempts to stop service instance

    Args:
        client: HttpClient to use
        srv_id: id of the service instance to stop
    """
    response = client.request(HttpMethod.PUT,
                              path="services/{srv_id}/stop",
                              path_params={'srv_id': srv_id},
                              raw_response=True,
                              msg="Stop service instance")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()


def restart_service(*, client: HttpClient, srv_id: str):
    """ PUT /services/{srv_id}/restart
    Attempts to restart service instance

    Args:
        client: HttpClient to use
        srv_id: id of the service instance to restart
    """
    response = client.request(HttpMethod.PUT,
                              path="services/{srv_id}/restart",
                              path_params={'srv_id': srv_id},
                              raw_response=True,
                              msg="Restart service instance")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response.json()

# --------------------------------------- application bindings --------------------------------------- #


def get_app_bindings(*, client: HttpClient, app_id: str):
    """ GET /applications/{app_id}/bindings """
    response = client.request(method=HttpMethod.GET,
                              path="applications/{app_id}/bindings",
                              path_params={'app_id': app_id},
                              msg="Get application bindings")
    return response["resources"]


def bind_svc(*, client: HttpClient, app_id, service_instance_id: str):
    """ POST applications/{app_id}/bindings """
    body = {
        'service_id': service_instance_id
    }
    return client.request(method=HttpMethod.POST,
                          path="applications/{app_id}/bindings",
                          path_params={'app_id': app_id},
                          body=body, msg="Bind service and app")


def unbind_svc(*, client: HttpClient, app_id: str, service_instance_id: str):
    """ DELETE /applications/{app_id}/bindings/services/{service_instance_id} """
    return client.request(method=HttpMethod.DELETE,
                          path="applications/{app_id}/bindings/services/{service_instance_id}",
                          path_params={'app_id': app_id, 'service_instance_id': service_instance_id},
                          msg="Unbind service from app")


# --------------------------------------- services --------------------------------------- #


def get_services(*, client: HttpClient, name: str=None, offering_id: str=None, plan_name: str=None, limit: int=None,
                 skip: int=None):
    """ GET /services """
    query_params = {
        "offering_id": offering_id,
        "plan_name": plan_name,
        "name": name,
        "limit": limit,
        "skip": skip
    }
    query_params = {k: v for k, v in query_params.items() if v is not None}
    return client.request(method=HttpMethod.GET, path="services", params=query_params, msg="List service instances")


def create_service(*, client: HttpClient, name: str=None, plan_id: str, offering_id: str, params: dict):
    """POST /services"""
    metadata = [{"key": "PLAN_ID", "value": plan_id}]
    if params is not None:
        metadata = metadata + [{"key": key, "value": val} for key, val in params.items()]
    body = {
        "metadata": metadata,
        "type": "SERVICE"
    }
    if client.url.rstrip('/').endswith(('/api/v1', '/api/v2')):
        body["classId"] = offering_id
    else:
        body["offeringId"] = offering_id
    if name is not None:
        body["name"] = name
    return client.request(method=HttpMethod.POST, path="services", body=body, msg="Create service instance")


def get_service(*, client: HttpClient, service_id: str):
    """ GET /services/{service_id} """
    return client.request(method=HttpMethod.GET,
                          path="services/{service_id}",
                          path_params={'service_id': service_id},
                          msg="Get service instance")


def delete_service(*, client: HttpClient, service_id: str):
    """ DELETE /services/{service_id} """
    return client.request(method=HttpMethod.DELETE,
                          path="services/{service_id}",
                          path_params={'service_id': service_id},
                          msg="Delete service instance")


def get_service_credentials(*, client: HttpClient, service_id: str):
    """ GET /services/{service_id}/credentials """
    return client.request(method=HttpMethod.GET,
                          path="services/{service_id}/credentials",
                          path_params={'service_id': service_id},
                          msg="Get service instance credentials")


def expose_service(*, client: HttpClient, service_id: str, should_expose: bool=True):
    """ PUT /services/{service_id}/expose """
    body = {
        "exposed": should_expose
    }
    return client.request(method=HttpMethod.PUT,
                          path="services/{service_id}/expose",
                          path_params={'service_id': service_id},
                          msg="Expose service instance", body=body)


def get_service_logs(*, client: HttpClient, service_id):
    """ GET /services/{service_id}/logs """
    return client.request(method=HttpMethod.GET, path="services/{service_id}/logs",
                          path_params={'service_id': service_id},
                          msg="Get service instance logs")


# --------------------------------------- service bindings --------------------------------------- #


def get_service_bindings(*, client: HttpClient, service_id: str):
    """ GET /services/{service_id}/bindings """
    response = client.request(method=HttpMethod.GET,
                              path="services/{service_id}/bindings",
                              path_params={'service_id': service_id},
                              msg="Get service bindings")
    return response["resources"]


def bind_service(*, client: HttpClient, service_id: str, application_id_to_bound=None, service_id_to_bound=None):
    """ POST /services/{service_id}/bindings """
    body = {}
    if application_id_to_bound is not None:
        body["application_id"] = application_id_to_bound
    if service_id_to_bound is not None:
        body["service_id"] = service_id_to_bound

    response = client.request(method=HttpMethod.POST,
                              path="services/{service_id}/bindings",
                              path_params={'service_id': service_id},
                              body=body,
                              raw_response=True,
                              msg="Bind service or application to service")
    return response


def unbind_app_from_service(*, client: HttpClient, service_id: str, application_id_to_unbound: str):
    """ DELETE /services/{service_id}/bindings/applications/{application_id_to_unbound} """
    return client.request(method=HttpMethod.DELETE,
                          path="services/{service_id}/bindings/applications/{application_id_to_unbound}",
                          path_params={'service_id': service_id,
                                       'application_id_to_unbound': application_id_to_unbound},
                          msg="Unbind app from service")


def unbind_svc_from_service(*, client: HttpClient, service_id: str, service_id_to_unbound: str):
    """ DELETE /services/{service_id}/bindings/services/{service_id_to_unbound} """
    return client.request(method=HttpMethod.DELETE,
                          path="services/{service_id}/bindings/services/{service_id_to_unbound}",
                          path_params={'service_id': service_id, 'service_id_to_unbound': service_id_to_unbound},
                          msg="Unbind service from service")


# --------------------------------------- users --------------------------------------- #

def get_users(*, client: HttpClient):
    """ GET /users """
    return client.request(method=HttpMethod.GET, path="users", msg="List users")


def delete_user(*, client: HttpClient, user_email: str):
    """ DELETE /users """
    body = {
        "email": user_email
    }
    return client.request(method=HttpMethod.GET, body=body, path="users", msg="Delete user")


def change_password(*, client: HttpClient, current_password: str, new_password: str):
    """ PUT /users/current/password """
    body = {
        "current_password": current_password,
        "new_password": new_password
    }
    return client.request(method=HttpMethod.PUT, body=body, path="users/current/password", msg="Change password")


# --------------------------------------- invitations --------------------------------------- #


def send_invitation(*, client: HttpClient, email: str):
    """ POST /users/invitations """
    body = {
        "email": email
    }
    return client.request(method=HttpMethod.POST, path="users/invitations", body=body, msg="Send invitation")


def get_invitations(*, client: HttpClient):
    """ GET /users/invitations """
    return client.request(method=HttpMethod.GET, path="users/invitations", msg="List invitations")


def delete_invitation(*, client: HttpClient, email: str):
    """ DELETE /users/invitations """
    body = {
        "email": email
    }
    return client.request(method=HttpMethod.DELETE, path="users/invitations", body=body, msg="Delete invitation")


def resend_invitation(*, client: HttpClient, email: str):
    """ POST /users/invitations/resend """
    body = {
        "email": email
    }
    return client.request(method=HttpMethod.POST, path="users/invitations/resend", body=body, msg="Resend invitation")


# --------------------------------------- metrics --------------------------------------- #


def get_metrics_single(*, client: HttpClient, metric_name: str, time_from: str=None, time_to: str=None):
    """ GET /metrics/single """
    body = {
        "metric": metric_name,
        "from": time_from,
        "to": time_to
    }
    return client.request(method=HttpMethod.GET, path="metrics/single", body=body, msg="Get single metric")


def get_metrics_platform(*, client: HttpClient, time_from: str=None, time_to: str=None):
    """ GET /metrics/platform """
    body = {
        "from": time_from,
        "to": time_to
    }
    return client.request(method=HttpMethod.GET, path="metrics/platform", body=body, msg="Get platform metrics")


def get_metrics_organizations(*, client: HttpClient, org_id: str, time_from: str=None, time_to: str=None):
    """ GET /metrics/organizations/{org_id} """
    body = {
        "from": time_from,
        "to": time_to
    }
    return client.request(method=HttpMethod.GET,
                          path="metrics/organizations/{org_id}",
                          path_params={'org_id': org_id},
                          body=body,
                          msg="Get organization metrics")

# --------------------------------------- platform info --------------------------------------- #

def get_platform_info(*, client: HttpClient) -> dict:
    """GET /platform_info

    Attempts to retrieve the platform info

    Args:
        client: HttpClient to use

    Return:
        Platform info as a dictionary
    """
    return client.request(method=HttpMethod.GET, path="platform_info",
                          msg="Get platform info")


def get_platform_components(*, client: HttpClient) -> dict:
    """GET /platform_components

    Attempts to retrieve the platform components

    Args:
        client: HttpClient to use

    Return:
        Platform components as a dictionary
    """
    return client.request(method=HttpMethod.GET, path="platform_components",
                          msg="Get platform components")

# --------------------------------------- CLI resources --------------------------------------- #

def get_cli_resource(*, client: HttpClient, resource_id: str):
    """ GET /resources/cli/{resource_id} """
    return client.request(method=HttpMethod.GET,
                          path="resources/cli/{resource_id}",
                          path_params={'resource_id': resource_id},
                          msg="Get CLI resource",
                          raw_response=True,
                          log_response_content=False)
