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

from modules.constants import HttpStatus, TapComponent as TAP
from modules.tap_object_model import Application, Buildpack, Organization, Platform, ServiceInstance, ServiceType, \
    Space, User
from modules.tap_logger import step
from tests.fixtures import assertions


logged_components = (TAP.platform_operations, )
pytestmark = [pytest.mark.components(TAP.platform_operations)]


@pytest.mark.skip(reason="Not yet adjusted to new TAP")
class TestNonAdminOperationsMetrics:

    @pytest.mark.skip("DPNG-5904")
    def test_non_admin_cannot_access_platform_operations(self, test_org_manager_client):
        step("Checking if non-admin user cannot retrieve data")
        assertions.assert_raises_http_exception(HttpStatus.CODE_UNAUTHORIZED, HttpStatus.MSG_UNAUTHORIZED,
                                                Platform().retrieve_metrics, test_org_manager_client)

    @pytest.mark.skip("DPNG-5904")
    def test_non_admin_user_cannot_access_refresh(self, test_org_manager_client):
        step("Checking if non-admin user cannot refresh data")
        assertions.assert_raises_http_exception(HttpStatus.CODE_UNAUTHORIZED, HttpStatus.MSG_UNAUTHORIZED,
                                                Platform.refresh_data, test_org_manager_client)


@pytest.mark.skip(reason="Not yet adjusted to new TAP")
class TestOperationsMetrics:
    """
    Operations Metrics test can be unstable when run parallel
    with other tests since it check for resources count
    """

    MAX_CHECK = 3
    cf_data = []
    platform_data = []

    def test_applications_metrics(self):
        step("Testing if CF values equals platform data. Data to check: applications count")
        assert self.assert_values("apps")

    def test_services_instances_metrics(self):
        step("Testing if CF values equals platform data. Data to check: services and user provided services count")
        assert self.assert_values("service_instances")

    def test_services_metrics(self):
        step("Testing if CF values equals platform data. Data to check: services and user provided services count")
        assert self.assert_values("services")

    def test_buildpacks_metrics(self):
        step("Testing if CF values equals platform data. Data to check: buildpack count")
        assert self.assert_values("buildpacks")

    def test_organizations_metrics(self):
        step("Testing if CF values equals platform data. Data to check: organizations count")
        assert self.assert_values("orgs")

    def test_spaces_metrics(self):
        step("Testing if CF values equals platform data. Data to check: spaces count")
        assert self.assert_values("spaces")

    def test_user_metrics(self):
        step("Testing if CF values equals platform data. Data to check: users count")
        assert self.assert_values("users")

    def assert_values(self, checked_metric):
        """
        this function is created to help with test instability when running in parallel
        with other tests. It assert if values are correct, if not it gather new data.
        This function should run max=MAX_CHECK times during this TestCase execution
        :param checked_metric: current metrics to check
        :return:
        """
        assert_result = self.check_if_contains(checked_metric)
        if assert_result:
            return assert_result,

        if len(self.platform_data) < self.MAX_CHECK:
            self.gather_all_data()
            return self.assert_values(checked_metric)
        else:
            return False, "Failed checked metrics {}, CF values: {}, platform operation metrics: {}".\
                format(checked_metric, self.get_cf_metrics(checked_metric), self.get_platform_metrics(checked_metric))

    def get_cf_metrics(self, checked_metric):
        return [getattr(x, checked_metric) for x in self.cf_data]

    def get_platform_metrics(self, checked_metric):
        return [getattr(x.metrics, checked_metric) for x in self.platform_data]

    def gather_all_data(self):
        platform = Platform()
        platform.retrieve_metrics(refresh=True)
        self.platform_data.append(platform)
        self.cf_data.append(CFData())

    def check_if_contains(self, checked_metric):
        cf_values = self.get_cf_metrics(checked_metric)
        platform_values = self.get_platform_metrics(checked_metric)
        return any(i in platform_values for i in cf_values)


class CFData(object):
    """
    helper class to collect all data from CF
    """

    def __init__(self):
        self.apps = len(Application.cf_api_get_list())
        self.service_instances = len(ServiceInstance.cf_api_get_list())
        self.services = len(ServiceType.cf_api_get_list())
        self.buildpacks = len(Buildpack.cf_api_get_list())
        self.orgs = len(Organization.cf_api_get_list())
        self.spaces = len(Space.cf_api_get_list())
        self.users = len(User.cf_api_get_all_users())
