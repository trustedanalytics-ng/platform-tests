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

from ..http_calls.platform import platform_operations


class PlatformInfo:

    def __init__(self, info):
        self.api_endpoint = info["api_endpoint"]
        self.cdh_version = info["cdh_version"]
        self.cli_url = info["cli_url"]
        self.cli_version = info["cli_version"]
        self.core_organization = info["core_organization"]
        self.external_tools = info["external_tools"]
        self.k8s_version = info["k8s_version"]
        self.platform_version = info["platform_version"]

    @classmethod
    def get(cls, client=None):
        """
        Retrieve info from platform using client api call.
        """
        return cls(platform_operations.api_get_platform_info(client))
