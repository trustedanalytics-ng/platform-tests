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

#region Images
def get_images():
    """ GET /images """
    return _get_client().request(HttpMethod.GET,
                                 path="images",
                                 msg="CATALOG: get images list")


def get_image(image_id):
    """ GET /images/{image_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="images/{}".format(image_id),
                                 msg="CATALOG: get image")


def create_image(image_type, state):
    """ POST /images """
    body = {
        "type": image_type,
        "state": state
    }
    response = _get_client().request(HttpMethod.POST,
                                     path="images",
                                     body=body,
                                     msg="CATALOG: create image")
    return response


def delete_image(image_id):
    """ DELETE /images/{image_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="images/{}".format(image_id),
                                     msg="CATALOG: delete image")
    return response


def update_image(image_id, field, value):
    """ PATCH /images/{image_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="images/{}".format(image_id),
                                     body=body,
                                     msg="CATALOG: updating image")
    return response
#endregion


#region Templates
def get_templates():
    """ GET /templates """
    return _get_client().request(HttpMethod.GET,
                                 path="templates",
                                 msg="CATALOG: get templates list")


def get_template(template_id):
    """ GET /templates/{template_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="templates/{}".format(template_id),
                                 msg="CATALOG: get template")


def create_template(state):
    """ POST /templates """
    body = {
        "templateId": "",
        "state": state
    }
    response = _get_client().request(HttpMethod.POST,
                                     path="templates",
                                     body=body,
                                     msg="CATALOG: create template")
    return response


def delete_template(template_id):
    """ DELETE /templates/{template_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="templates/{}".format(template_id),
                                     msg="CATALOG: delete template")
    return response


def update_template(template_id, field, value):
    """ PATCH /templates/{template_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="templates/{}".format(template_id),
                                     body=body,
                                     msg="CATALOG: updating template")
    return response
#endregion


#region Instances
def get_instances():
    """ GET /instances """
    return _get_client().request(HttpMethod.GET,
                                 path="instances",
                                 msg="CATALOG: get instances list")


def get_instance(instance_id):
    """ GET /instances/{instance_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="instances/{}".format(instance_id),
                                 msg="CATALOG: get instance")


def delete_instance(instance_id):
    """ DELETE /instances/{instance_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="instances/{}".format(instance_id),
                                     msg="CATALOG: delete instance")
    return response


def update_instance(instance_id, field, value):
    """ PATCH /instances/{instance_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="instances/{}".format(instance_id),
                                     body=body,
                                     msg="CATALOG: updating instance")
    return response
#endregion


#region Services
def get_services():
    """ GET /services """
    return _get_client().request(HttpMethod.GET,
                                 path="services",
                                 msg="CATALOG: get services list")


def get_service(service_id):
    """ GET /services/{service_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{}".format(service_id),
                                 msg="CATALOG: get service")


def create_service(body):
    """ POST /services """
    response = _get_client().request(HttpMethod.POST,
                                     path="services",
                                     body=body,
                                     msg="CATALOG: create service")
    return response


def delete_service(service_id):
    """ DELETE /services/{service_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="services/{}".format(service_id),
                                     msg="CATALOG: delete service")
    return response


def update_service(service_id, field, value):
    """ PATCH /services/{service_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="services/{}".format(service_id),
                                     body=body,
                                     msg="CATALOG: updating service")
    return response


def create_service_instance(service_id, body):
    """ POST /services/{service_id}/instances """
    response = _get_client().request(HttpMethod.POST,
                                     path="services/{}/instances".format(service_id),
                                     body=body,
                                     msg="CATALOG: create service instance")
    return response


def get_all_services_instances():
    """ GET /services/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="services/instances",
                                 msg="CATALOG: get all services instances list")


def get_service_instances(service_id):
    """ GET /services/{serviceId}/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{}/instances".format(service_id),
                                 msg="CATALOG: get instances list")


def get_service_instance(service_id, instance_id):
    """ GET /services/{serviceId}/instances/{instance_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{}/instances/{}".format(service_id, instance_id),
                                 msg="CATALOG: get instance")


def update_service_instance(service_id, instance_id, field, value):
    """ PATCH /services/{service_id}/instances/{instance_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="services/{}/instances/{}".format(service_id, instance_id),
                                     body=body,
                                     msg="CATALOG: updating service")
    return response


def delete_service_instance(service_id, instance_id):
    """ DELETE /services/{service_id}/instances/{instance_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="services/{}/instances/{}".format(service_id, instance_id),
                                     msg="CATALOG: delete service")
    return response


def get_service_plans(service_id):
    """ GET /services/{serviceId}/plans """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{}/plans".format(service_id),
                                 msg="CATALOG: get service plans list")


def get_service_plan(service_id, plan_id):
    """ GET /services/{serviceId}/plans/{planId} """
    return _get_client().request(HttpMethod.GET,
                                 path="services/{}/plans/{}".format(service_id, plan_id),
                                 msg="CATALOG: get service plan by Id")


def delete_service_plan(service_id, plan_id):
    """ DELETE /services/{serviceId}/plans/{planId} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="services/{}/plans/{}".format(service_id, plan_id),
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
                                     path="services/{}/plans/{}".format(service_id, plan_id),
                                     body=body,
                                     msg="CATALOG: updating service plan")
    return response


def create_service_plan(service_id, body):
    """ POST /services/{service_id}/plans """
    response = _get_client().request(HttpMethod.POST,
                                     path="services/{}/plans".format(service_id),
                                     body=body,
                                     msg="CATALOG: create service plan")
    return response


#endregion


#region Applications
def create_application(name, template_id, image_id):
    """ POST /applications """
    body = {
        "name": name,
        "imageId": image_id,
        "templateId": template_id,
        "replication": 0
    }
    response = _get_client().request(HttpMethod.POST,
                                     path="applications",
                                     body=body,
                                     msg="CATALOG: create application")
    return response


def get_applications():
    """ GET /applications """
    return _get_client().request(HttpMethod.GET,
                                 path="applications",
                                 msg="CATALOG: get applications list")


def get_application(application_id):
    """ GET /applications/{application_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/{}".format(application_id),
                                 msg="CATALOG: get application")


def delete_application(application_id):
    """ DELETE /applications/{application_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="applications/{}".format(application_id),
                                     msg="CATALOG: delete application")
    return response


def update_application(application_id, field, value):
    """ PATCH /applications/{application_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="applications/{}".format(application_id),
                                     body=body,
                                     msg="CATALOG: updating application")
    return response


def create_application_instance(application_id, body):
    """ POST /applications/{application_id}/instances """
    response = _get_client().request(HttpMethod.POST,
                                     path="applications/{}/instances".format(application_id),
                                     body=body,
                                     msg="CATALOG: create application instance")
    return response


def get_all_applications_instances():
    """ GET /applications/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/instances",
                                 msg="CATALOG: get all applications instances list")


def get_application_instances(application_id):
    """ GET /applications/{application_id}/instances """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/{}/instances".format(application_id),
                                 msg="CATALOG: get application instances list")


def get_application_instance(application_id, instance_id):
    """ GET /applications/{application_id}/instances/{instance_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="applications/{}/instances/{}".format(application_id, instance_id),
                                 msg="CATALOG: get application instance")


def delete_application_instance(application_id, instance_id):
    """ DELETE /applications/{application_id}/instances/{instance_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="applications/{}/instances/{}".format(application_id, instance_id),
                                     msg="CATALOG: delete application instance")
    return response


def update_application_instance(application_id, instance_id, field, value):
    """ PATCH /applications/{application_id}/instances/{instance_id} """
    body = [{
        "op": "Update",
        "field": field,
        "value": value
    }]
    response = _get_client().request(HttpMethod.PATCH,
                                     path="applications/{}/instances/{}".format(application_id, instance_id),
                                     body=body,
                                     msg="CATALOG: updating application instance")
    return response
#endregion
