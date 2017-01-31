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

from modules.constants import TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from tap_component_config import TAP_core_services


def _get_client():
    api_version = TAP_core_services[TapComponent.catalog]["api_version"]
    configuration = K8sServiceConfigurationProvider.get(TapComponent.catalog,
                                                        api_endpoint="api/{}".format(api_version))
    return HttpClientFactory.get(configuration)


# ------------------------------------------------------ images ------------------------------------------------------ #

def get_images():
    """ GET /images """
    return _get_client().request(HttpMethod.GET,
                                 path="images",
                                 msg="CATALOG: get image list")


def get_image(*, image_id):
    """ GET /images/{image_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="images/{image_id}",
                                 path_params={'image_id': image_id},
                                 msg="CATALOG: get image")


def create_image(*, image_id, image_type, state, blob_type):
    """ POST /images """
    body = {
        "id": image_id,
        "type": image_type,
        "state": state,
        "blobType": blob_type
    }
    body = {k: v for k, v in body.items() if v is not None}
    response = _get_client().request(HttpMethod.POST,
                                     path="images",
                                     body=body,
                                     msg="CATALOG: create image")
    return response


def delete_image(*, image_id):
    """ DELETE /images/{image_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="images/{image_id}",
                                     path_params={'image_id': image_id},
                                     msg="CATALOG: delete image")
    return response


def update_image(*, image_id, field_name, value, prev_value=None, username=None):
    """ PATCH /images/{image_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prevValue": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="images/{image_id}",
                                     path_params={'image_id': image_id},
                                     body=body,
                                     msg="CATALOG: update image")
    return response


# ---------------------------------------------------- templates ---------------------------------------------------- #


def get_templates():
    """ GET /templates """
    return _get_client().request(HttpMethod.GET,
                                 path="templates",
                                 msg="CATALOG: get template list")


def get_template(*, template_id):
    """ GET /templates/{template_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="templates/{template_id}",
                                 path_params={'template_id': template_id},
                                 msg="CATALOG: get template")


def create_template(*, state, template_id=None):
    """ POST /templates """
    body = {
        "templateId": template_id,
        "state": state
    }
    body = {k: v for k, v in body.items() if v is not None}
    response = _get_client().request(HttpMethod.POST,
                                     path="templates",
                                     body=body,
                                     msg="CATALOG: create template")
    return response


def delete_template(*, template_id):
    """ DELETE /templates/{template_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="templates/{template_id}",
                                     path_params={'template_id': template_id},
                                     msg="CATALOG: delete template")
    return response


def update_template(*, template_id, field_name, value, prev_value=None, username=None):
    """ PATCH /templates/{template_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prevValue": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="templates/{template_id}",
                                     path_params={'template_id': template_id},
                                     body=body,
                                     msg="CATALOG: update template")
    return response


# ---------------------------------------------------- instances ---------------------------------------------------- #

def get_instances():
    """ GET /instances """
    return _get_client().request(HttpMethod.GET,
                                 path="instances",
                                 msg="CATALOG: get instances list")


def get_instance(*, instance_id):
    """ GET /instances/{instance_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="instances/{instance_id}",
                                 path_params={'instance_id': instance_id},
                                 msg="CATALOG: get instance")


def delete_instance(*, instance_id):
    """ DELETE /instances/{instance_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="instances/{instance_id}",
                                     path_params={'instance_id': instance_id},
                                     msg="CATALOG: delete instance")
    return response


def update_instance(*, instance_id, field_name, value, prev_value=None, username=None):
    """ PATCH /instances/{instance_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prev_value": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="instances/{instance_id}",
                                     path_params={'instance_id': instance_id},
                                     body=body,
                                     msg="CATALOG: updating instance")
    return response


# ----------------------------------------------------- services ----------------------------------------------------- #


def get_services():
    """ GET /services """
    return _get_client().request(HttpMethod.GET,
                                 path="services",
                                 msg="CATALOG: get services list")


def get_service(*, service_id):
    """ GET /services/{service_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{service_id}",
                                 path_params={'service_id': service_id},
                                 msg="CATALOG: get service")


def create_service(*, template_id, name, description=None, bindable=True, state=None, plans=None):
    """ POST /services """
    body = {
        "templateId": template_id,
        "name": name,
        "description": description,
        "bindable": bindable,
        "state": state,
        "plans": plans
    }
    response = _get_client().request(HttpMethod.POST,
                                     path="services",
                                     body=body,
                                     msg="CATALOG: create service")
    return response


def delete_service(*, service_id):
    """ DELETE /services/{service_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="services/{service_id}",
                                     path_params={'service_id': service_id},
                                     msg="CATALOG: delete service")
    return response


def update_service(*, service_id, field_name, value, prev_value=None, username=None):
    """ PATCH /services/{service_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prevValue": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="services/{service_id}",
                                     path_params={'service_id': service_id},
                                     body=body,
                                     msg="CATALOG: updating service")
    return response


# ------------------------------------------------ service instances ------------------------------------------------ #


def create_service_instance(*, service_id, name, instance_type, state, metadata=None):
    """ POST /services/{service_id}/instances """
    body = {
        "name": name,
        "type": instance_type,
        "state": state
    }
    if metadata is not None:
        body["metadata"] = metadata
    body = {k: v for k, v in body.items() if v is not None}
    response = _get_client().request(HttpMethod.POST,
                                     path="services/{service_id}/instances",
                                     path_params={'service_id': service_id},
                                     body=body,
                                     msg="CATALOG: create service instance")
    return response


def get_all_service_instances():
    """ GET /services/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="services/instances",
                                 msg="CATALOG: get list of all service instances")


def get_service_instances(*, service_id):
    """ GET /services/{serviceId}/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{service_id}/instances",
                                 path_params={'service_id': service_id},
                                 msg="CATALOG: get instances of a service")


def get_service_instance(*, service_id, instance_id):
    """ GET /services/{serviceId}/instances/{instance_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{service_id}/instances/{instance_id}",
                                 path_params={'service_id': service_id, 'instance_id': instance_id},
                                 msg="CATALOG: get service instance")


def update_service_instance(*, service_id, instance_id, field_name, value, prev_value=None, username=None):
    """ PATCH /services/{service_id}/instances/{instance_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prevValue": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="services/{service_id}/instances/{instance_id}",
                                     path_params={'service_id': service_id, 'instance_id': instance_id},
                                     body=body,
                                     msg="CATALOG: update service instance")
    return response


def delete_service_instance(*, service_id, instance_id):
    """ DELETE /services/{service_id}/instances/{instance_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="services/{service_id}/instances/{instance_id}",
                                     path_params={'service_id': service_id, 'instance_id': instance_id},
                                     msg="CATALOG: delete service")
    return response


# -------------------------------------------------- service plans -------------------------------------------------- #

def get_service_plans(service_id):
    """ GET /services/{serviceId}/plans """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{service_id}/plans",
                                 path_params={'service_id': service_id},
                                 msg="CATALOG: get service plans list")


def get_service_plan(service_id, plan_id):
    """ GET /services/{serviceId}/plans/{planId} """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{service_id}/plans/{plan_id}",
                                 path_params={'service_id': service_id, 'plan_id': plan_id},
                                 msg="CATALOG: get service plan by Id")


def delete_service_plan(service_id, plan_id):
    """ DELETE /services/{serviceId}/plans/{planId} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="services/{service_id}/plans/{plan_id}",
                                     path_params={'service_id': service_id, 'plan_id': plan_id},
                                     msg="CATALOG: delete service plan")
    return response


def update_service_plan(service_id, plan_id, field, value):
    """ PATCH /services/{serviceId}/plans/{planId} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="services/{service_id}/plans/{plan_id}",
                                     path_params={'service_id': service_id, 'plan_id': plan_id},
                                     body=body,
                                     msg="CATALOG: updating service plan")
    return response


def create_service_plan(service_id, body):
    """ POST /services/{service_id}/plans """
    response = _get_client().request(HttpMethod.POST,
                                     path="services/{service_id}/plans",
                                     path_params={'service_id': service_id},
                                     body=body,
                                     msg="CATALOG: create service plan")
    return response


# --------------------------------------------------- applications --------------------------------------------------- #


def create_application(*, name, template_id, image_id, replication, description=None):
    """ POST /applications """
    body = {
        "name": name,
        "imageId": image_id,
        "templateId": template_id,
        "replication": replication,
        "description": description
    }
    body = {k: v for k, v in body.items() if v is not None}
    response = _get_client().request(HttpMethod.POST,
                                     path="applications",
                                     body=body,
                                     msg="CATALOG: create application")
    return response


def get_applications():
    """ GET /applications """
    return _get_client().request(HttpMethod.GET,
                                 path="applications",
                                 msg="CATALOG: get application list")


def get_application(*, application_id):
    """ GET /applications/{application_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/{application_id}",
                                 path_params={'application_id': application_id},
                                 msg="CATALOG: get application")


def update_application(*, application_id, field_name, value, prev_value=None, username=None):
    """ PATCH /applications/{application_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prevValue": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="applications/{application_id}",
                                     path_params={'application_id': application_id},
                                     body=body,
                                     msg="CATALOG: update application")
    return response


def delete_application(application_id):
    """ DELETE /applications/{application_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="applications/{application_id}",
                                     path_params={'application_id': application_id},
                                     msg="CATALOG: delete application")
    return response


def create_application_instance(*, application_id, name, instance_type, state):
    """ POST /applications/{application_id}/instances """
    body = {
        "name": name,
        "type": instance_type,
        "state": state
    }
    response = _get_client().request(HttpMethod.POST,
                                     path="applications/{application_id}/instances",
                                     path_params={'application_id': application_id},
                                     body=body,
                                     msg="CATALOG: create application instance")
    return response


# ---------------------------------------------- application instances ---------------------------------------------- #

def get_all_application_instances():
    """ GET /applications/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/instances",
                                 msg="CATALOG: get all application instances")


def get_application_instances(*, application_id):
    """ GET /applications/{application_id}/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/{application_id}/instances",
                                 path_params={'application_id': application_id},
                                 msg="CATALOG: get instances of an application")


def get_application_instance(*, application_id, instance_id):
    """ GET /applications/{application_id}/instances/{instance_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/{application_id}/instances/{instance_id}",
                                 path_params={'application_id': application_id, 'instance_id': instance_id},
                                 msg="CATALOG: get application instance")


def update_application_instance(*, application_id, instance_id, field_name, value, prev_value=None, username=None):
    """ PATCH /applications/{application_id}/instances/{instance_id} """
    body = [{
        "op": "Update",
        "field": field_name,
        "value": value,
        "prevValue": prev_value,
        "username": username
    }]
    body = [{k: v for k, v in body[0].items() if v is not None}]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="applications/{application_id}/instances/{instance_id}",
                                     path_params={'application_id': application_id, 'instance_id': instance_id},
                                     body=body,
                                     msg="CATALOG: updating application instance")
    return response


def delete_application_instance(*, application_id, instance_id):
    """ DELETE /applications/{application_id}/instances/{instance_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="applications/{application_id}/instances/{instance_id}",
                                     path_params={'application_id': application_id, 'instance_id': instance_id},
                                     msg="CATALOG: delete application instance")
    return response

# ---------------------------------------------- readiness probe ---------------------------------------------- #


def get_stable_state():
    """ GET /stable-state """
    return _get_client().request(HttpMethod.GET, path="stable-state", msg="CATALOG: get stable-state")
