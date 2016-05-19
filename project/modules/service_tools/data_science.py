#
# Copyright (c) 2016 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json

import requests
from retry import retry

from ..exceptions import UnexpectedResponseError
from ..tap_logger import log_http_request, log_http_response
from configuration import config
from ..tap_object_model import ServiceInstance
from ..test_names import generate_test_object_name


class DataScience(object):

    def __init__(self, org_guid, space_guid, service_label, service_plan_name, instance_name=None, params=None):
        if instance_name is None:
            instance_name = generate_test_object_name()
        self.login = None
        self.password = None
        self.instance_url = None
        self.session = requests.Session()

        self.instance = ServiceInstance.api_create_with_plan_name(org_guid=org_guid, space_guid=space_guid,
                                                                  name=instance_name, service_label=service_label,
                                                                  service_plan_name=service_plan_name, params=params)

    def request(self, method, instance_url, endpoint, username, body=None, data=None, params=None, files=None,
                message_on_error=""):
        request = requests.Request(
            method=method,
            url="http://{}/{}".format(instance_url, endpoint),
            data=data,
            params=params,
            json=body,
            files=files
        )
        request = self.session.prepare_request(request)
        log_http_request(request, username=username, password=self.password)
        response = self.session.send(request, timeout=90)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(status=response.status_code, error_message=message_on_error)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    @retry(KeyError, tries=5, delay=5)
    def get_credentials(self):
        response = self.instance.api_get_credentials()
        self.login = response["login"]
        self.password = response["password"]
        self.instance_url = response["hostname"]
