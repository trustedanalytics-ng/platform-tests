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
import modules.http_calls.kubernetes as k8s


class K8sService(object):

    def __init__(self, name, host, port):
        self.name = name
        self.url = "{}://{}:{}".format(config.ng_service_http_scheme, host, port)

    def __repr__(self):
        return "{} (name={}, url={})".format(self.__class__.__name__, self.name, self.url)

    @classmethod
    def _from_k8s_response(cls, response):
        return cls(name=response["metadata"]["name"],
                   host=response["spec"]["clusterIP"],
                   port=response["spec"]["ports"][0]["port"])

    @classmethod
    def get(cls, service_name):
        response = k8s.k8s_get_service(service_name)
        return cls._from_k8s_response(response)

    @classmethod
    def get_list(cls):
        response = k8s.k8s_get_services()
        services = []
        for item in response["items"]:
            service = cls._from_k8s_response(item)
            services.append(service)
        return services
