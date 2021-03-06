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

from tap_component_config import TAP_core_services
from modules.constants import TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from modules.constants import HttpStatus


def _get_client():
    api_version = TAP_core_services[TapComponent.image_factory]["api_version"]
    configuration = K8sServiceConfigurationProvider.get(TapComponent.image_factory,
                                                        api_endpoint="api/{}".format(api_version))
    return HttpClientFactory.get(configuration)


def create_image(body=None, *, image_id):
    """ POST /image """
    if body is None:
        body = {
            "id": image_id
            }
    response = _get_client().request(HttpMethod.POST,
                                     path="image",
                                     body=body,
                                     raw_response=True, raise_exception=True,
                                     msg="IMAGE FACTORY: create image")
    assert response.status_code == HttpStatus.CODE_ACCEPTED
    return response


def delete_image(*, image_id):
    """ DELETE /image/{image_id} """
    response = _get_client().request(HttpMethod.DELETE,
                                     path="image/{image_id}",
                                     path_params={'image_id': image_id},
                                     raw_response=True, raise_exception=True,
                                     msg="IMAGE FACTORY: delete image")
    return response

