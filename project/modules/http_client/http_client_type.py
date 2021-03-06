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

from enum import Enum


class HttpClientType(Enum):
    """Http client types."""

    BASIC_AUTH = "BasicAuth"
    UAA = "UserAccountAndAuthentication"
    CONSOLE = "Console"
    NO_AUTH = "No Auth"
    APPLICATION = "Application"
    CLOUD_FOUNDRY = "CloudFoundry"
    BROKER = "Broker"
    WEBHDFS = "Webhdfs"
    CLOUDERA = "Cloudera"
    K8S_SERVICE = "K8SService"
