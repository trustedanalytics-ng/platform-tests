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

from modules.tap_object_model import Binding

APP_GUID = "e7b9e322-5c25-4a12-41e8-e2b69133b4ab"
SERVICE_INSTANCE_GUID = "15a0dd59-87bd-4018-7563-bc69448238fb"
SERVICE_INSTANCE_NAME = "bindtest"

GET_RESPONSE = {
    'entity': {
        'service_instance_name': SERVICE_INSTANCE_NAME,
        'app_guid': APP_GUID,
        'service_instance_guid': SERVICE_INSTANCE_GUID
    }
}


class TestServiceBinding:
    def test_binding_from_response(self):
        binding = Binding._from_response(GET_RESPONSE)
        assert binding.app_guid == APP_GUID
        assert binding.service_instance_guid == SERVICE_INSTANCE_GUID
        assert binding.service_instance_name == SERVICE_INSTANCE_NAME
