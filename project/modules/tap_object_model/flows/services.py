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

from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceKey
from tests.fixtures.assertions import assert_equal_with_retry, assert_instance_in_space, assert_instance_not_in_space


def get_service_keys(instance):
    summary = ServiceInstance.api_get_keys(instance.space_guid)
    assert instance in summary
    return summary[instance]


def create_instance_and_key_then_delete_key_and_instance(context, org, space, other_space, service_label, plan, client=None):
    step("Testing service {} plan {}".format(service_label, plan["name"]))
    instance = create_instance(context, org.guid, space.guid, service_label, plan["guid"], client=client)
    assert_instance_in_space(instance, space)
    assert_instance_not_in_space(instance, other_space)
    instance_key = create_key(instance, space.guid, client=client)
    delete_key(instance, instance_key, space.guid, client=client)
    delete_instance(instance, space.guid, client=client)


def create_instance(context, org_guid, space_guid, service_label, plan_guid, params=None, client=None):
    step("Create service instance")
    instance = ServiceInstance.api_create(context=context, org_guid=org_guid, space_guid=space_guid, client=client,
                                          service_label=service_label, service_plan_guid=plan_guid, params=params)
    step("Check that the instance was created")
    instance.ensure_created()
    return instance


def delete_instance(instance, space_guid, client=None):
    step("Delete the instance")
    instance.api_delete(client=client)
    step("Check that the instance was deleted")
    instances = ServiceInstance.api_get_list(space_guid=space_guid)
    assert instance not in instances


def create_key(instance, space_guid, client=None):
    step("Check that the instance exists in summary and has no service keys")
    assert_equal_with_retry(expected_value=[], callableObj=get_service_keys, instance=instance)
    step("Create a key for the instance and check it's correct")
    instance_key = ServiceKey.api_create(instance.guid, client=client)
    summary = ServiceInstance.api_get_keys(space_guid)
    assert summary[instance][0] == instance_key
    return instance_key


def delete_key(instance, instance_key, space_guid, client=None):
    step("Delete key and check that it's deleted")
    instance_key.api_delete(client=client)
    summary = ServiceInstance.api_get_keys(space_guid)
    assert summary[instance] == []
