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

from modules.constants import TapMessage
import modules.http_calls.platform.container_broker as container_broker_api


class ContainerBrokerInstance(object):
    ENVS_KEY = "Envs"

    def __init__(self, *, instance_id: str):
        """Instantiate objects of this class using catalog service instance id"""
        self.id = instance_id

    def get_logs(self):
        response = container_broker_api.get_logs(instance_id=self.id)
        return response

    def get_envs(self):
        response = container_broker_api.get_envs(instance_id=self.id)
        return response

    def bind(self, bound_instance_id):
        response = container_broker_api.bind_service_instances(src_instance_id=self.id,
                                                               dst_instance_id=bound_instance_id)
        assert response["message"] == TapMessage.SUCCESS

    def unbind(self, bound_instance_id):
        response = container_broker_api.unbind_service_instances(src_instance_id=self.id,
                                                                 dst_instance_id=bound_instance_id)
        assert response["message"] == TapMessage.SUCCESS

    def scale(self, instance_number):
        response = container_broker_api.scale_service_instance(instance_id=self.id, replicas=instance_number)
        assert response["message"] == TapMessage.SUCCESS
