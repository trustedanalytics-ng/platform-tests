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


def _get_client():
    configuration = K8sServiceConfigurationProvider.get(TapComponent.template_repository.value, api_endpoint="api/v1")
    return HttpClientFactory.get(configuration)


def get_templates():
    """ GET /templates """
    return _get_client().request(HttpMethod.GET,
                                 path="templates",
                                 msg="TEMPLATE REPOSITORY: get template list")


def get_template(template_id):
    """ GET /templates/{template_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="templates/{}".format(template_id),
                                 msg="TEMPLATE REPOSITORY: get template")


def create_template(template_id, template_body, hooks):
    """ POST /templates """
    body = {
        "id": template_id,
        "body": template_body,
        "hooks": hooks
    }
    response = _get_client().request(HttpMethod.POST,
                                 path="templates",
                                 body=body,
                                 msg="TEMPLATE REPOSITORY: create template")
    return response


def get_parsed_template(template_id, service_id):
    """ GET /parsed_template/{template_id} """
    return _get_client().request(HttpMethod.GET,
                                 path="parsed_template/{}".format(template_id),
                                 params={"serviceId": service_id},
                                 msg="TEMPLATE REPOSITORY: get parsed template")


def delete_template(template_id):
    """ DELETE /templates/{template_id} """
    return _get_client().request(HttpMethod.DELETE,
                                 path="templates/{}".format(template_id),
                                 msg="TEMPLATE REPOSITORY: delete template")