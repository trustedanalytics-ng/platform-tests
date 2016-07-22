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

import config
from modules.constants import TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider


def _get_client(api_endpoint="api/{}".format(config.ng_component_api_version)):
    configuration = K8sServiceConfigurationProvider.get(TapComponent.catalog.value, api_endpoint=api_endpoint)
    return HttpClientFactory.get(configuration)


def get_images():
    """ GET /images """
    return _get_client().request(HttpMethod.GET,
                                 path="images",
                                 msg="CATALOG: get images list")


def get_image(image_id, api_endpoint="api/{}".format(config.ng_component_api_version)):
    """ GET /images/{image_id} """
    return _get_client(api_endpoint).request(HttpMethod.GET,
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
