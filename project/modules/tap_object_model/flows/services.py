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

from modules.tap_object_model import ServiceInstance, ServiceKey
from modules.tap_logger import step
from tests.fixtures import assertions


def get_service_keys(instance):
    summary = ServiceInstance.api_get_keys(instance.space_guid)
    assert instance in summary
    return summary[instance]


def create_instance_and_key_then_delete_key_and_instance(org_guid, space_guid, service_label, plan_guid, plan_name):
    step("Create instance ({} - {})".format(service_label, plan_name))
    instance = ServiceInstance.api_create(
        org_guid=org_guid,
        space_guid=space_guid,
        service_label=service_label,
        service_plan_guid=plan_guid
    )
    step("Check that the instance was created ({} - {})".format(service_label, plan_name))
    instance.ensure_created()
    service_key_exception = None
    try:
        step("Check that the instance exists in summary and has no keys ({} - {})".format(service_label, plan_name))
        assertions.assert_equal_with_retry(expected_value=[], callableObj=get_service_keys, instance=instance)
        step("Create a key for the instance and check it's correct ({} - {})".format(service_label, plan_name))
        instance_key = ServiceKey.api_create(instance.guid)
        summary = ServiceInstance.api_get_keys(space_guid)
        assert summary[instance][0] == instance_key
        step("Delete key and check that it's deleted ({} - {})".format(service_label, plan_name))
        instance_key.api_delete()
        summary = ServiceInstance.api_get_keys(space_guid)
        assert summary[instance] == []
    except AssertionError as e:
        service_key_exception = e
    try:
        step("Delete the instance ({} - {})".format(service_label, plan_name))
        instance.api_delete()
        step("Check that the instance was deleted ({} - {})".format(service_label, plan_name))
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        assert instance not in instances
    except AssertionError as e:
        if service_key_exception is None:
            service_key_exception = e
    if service_key_exception is not None:
        raise service_key_exception

