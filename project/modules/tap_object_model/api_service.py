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

import modules.http_calls.platform.api_service as api_service


class ApiService(object):

    @classmethod
    def push_application(cls, file_path=None, manifest_path=None):
        response = api_service.push_application(file_path, manifest_path)
        return response

    @classmethod
    def delete_application(cls, id):
        response = api_service.delete_application(id)
        return response

    @classmethod
    def get_applications(cls):
        return api_service.get_applications()

    @classmethod
    def get_application(cls, id):
        return api_service.get_application(id)

    @classmethod
    def scale_application(cls, id, replicas):
        return api_service.scale_application(id, replicas)

    @classmethod
    def get_application_logs(cls, id):
        return api_service.get_application_logs(id)

    @classmethod
    def stop_application(cls, id):
        return api_service.stop_application(id)

    @classmethod
    def start_application(cls, id):
        return api_service.start_application(id)
