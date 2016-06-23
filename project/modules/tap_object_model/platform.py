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

from retry import retry

from ..http_calls.platform import platform_operations


class Platform(object):
    """
    this object should contain methods and fields that are general to whole platform.
    """

    def retrieve_metrics(self, client=None, refresh=False):
        """
        retrive basics metrics from platform using client api call.
        If refresh is True, this call can take time, depending on platform size
        :param refresh should data be refreshed? could take time
        :return:
        """
        metrics_data = platform_operations.api_get_platform_operations(client)

        if refresh:
            self.refresh_data(client)
            # to consider in needed in future: parse metrics to platform fields
            metrics_data = self._check_for_refreshed_data(metrics_data["timestamp"], client)

        self.metrics = PlatformMetrics(metrics_data)

    @staticmethod
    @retry(AssertionError, tries=30, delay=10)
    def _check_for_refreshed_data(timestamp, client=None):
        """
        function check if data on platform are refreshed
        this should be call before creating any additional resources for example: orgs, spaces, users,...
        tries - number of check performed
        delay - time between tries, in seconds
        :param timestamp: timestamp of previous call
        :return: platform metrics
        """
        metrics = platform_operations.api_get_platform_operations(client)
        if timestamp == metrics["timestamp"]:
            txt = "retrieved metrics from previous timestamp, previous {}, retrieved: {}".format(timestamp,
                                                                                                 metrics["timestamp"])
            raise AssertionError(txt)
        return metrics

    @staticmethod
    def refresh_data(client=None):
        """
        trigger refresh operations.
        :param client: user used for refresh operations. Default
        :return:
        """
        platform_operations.api_refresh_platform_operations(client)


class PlatformMetrics(object):

    def __init__(self, platform):
        self.apps = platform["controllerSummary"]["appCount"]
        self.service_instances = platform["controllerSummary"].get("serviceInstancesCount", 0)
        self.services = platform["controllerSummary"]["serviceCount"]
        self.buildpacks = platform["controllerSummary"]["buildpackCount"]
        self.orgs = platform["controllerSummary"]["orgCount"]
        self.spaces = platform["controllerSummary"]["spaceCount"]
        self.users = platform["controllerSummary"]["userCount"]
        self.buildpacks_data = platform["controllerSummary"]["buildpacks"]
