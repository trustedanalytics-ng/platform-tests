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

from tap_ng_component_config import k8s_core_services
from modules.constants import TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider


def _get_client():
    api_version = k8s_core_services[TapComponent.catalog]["api_version"]
    configuration = K8sServiceConfigurationProvider.get(TapComponent.catalog.value,
                                                        api_endpoint="api/{}".format(api_version))
    return HttpClientFactory.get(configuration)


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
