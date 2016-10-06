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

import pytest

from modules.constants import ApiServiceHttpStatus
from modules.tap_logger import step
from modules.tap_object_model import ServiceOffering
from tests.fixtures.assertions import assert_raises_http_exception


@pytest.mark.skip("DPNG-10981[api-tests] Refactor TAP CLI tests")
class TestApiServiceOfferings:

    @pytest.mark.bugs("DPNG-10996 [TAP-NG] Unable to delete service offering")
    def test_create_and_delete_new_offering(self, context):
        step("Create new offering")
        test_offering = ServiceOffering.create(context)
        step("Check that the new offering is in catalog")
        catalog = ServiceOffering.get_list()
        assert test_offering in catalog
        step("Get the offering")
        offering = ServiceOffering.get(test_offering.guid)
        assert test_offering == offering
        step("Delete the offering")
        test_offering.delete()
        step("Check that the offering is no longer in catalog")
        catalog = ServiceOffering.get_list()
        assert test_offering not in catalog
        step("Check that requesting the deleted offering returns an error")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, ApiServiceHttpStatus.MSG_KEY_NOT_FOUND,
                                     test_offering.delete)

    def test_cannot_create_the_same_offering_twice(self, context):
        step("Create new offering")
        test_offering = ServiceOffering.create(context)
        step("Check that the offering exists")
        catalog = ServiceOffering.get_list()
        assert test_offering in catalog
        step("Try creating offering with name of an already existing offering")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_CONFLICT,
                                     ApiServiceHttpStatus.MSG_SERVICE_ALREADY_EXISTS.format(test_offering.label),
                                     ServiceOffering.create, context, label=test_offering.label)
        step("Check that catalog has not changed")
        assert sorted(ServiceOffering.get_list()) == sorted(catalog)

