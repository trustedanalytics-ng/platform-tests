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

ng_catalog_instance_correct_body = {
    "type": "service",
    "name": "instance-name-",
    "state": "requested",
    "metadata": [
        {
            "key": "nginx",
            "value": "4"
        }
    ]
}

ng_catalog_instance_no_metadata_body = {
    "id": "",
    "name": "instance-name-",
    "type": "service",
    "classId": "90-830473249534-50294",
    "state": "requested",
    "metadata": [
        {}
    ],
    "bindings": [
        {}
    ]
}

ng_catalog_instance_bad_name_body = {
    "type": "service",
    "name": "instance-name!#%-",
    "state": "requested",
    "metadata": [
        {
            "key": "nginx",
            "value": "4"
        }
    ]
}

ng_catalog_service_correct_body = {
    "name": "service-name-",
    "bindable": False,
    "templateId": "template-id-",
    "plans": None
}
