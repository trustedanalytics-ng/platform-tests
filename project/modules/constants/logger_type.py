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


class LoggerType(object):
    """Logger types definitions"""

    CF_CLI = "CF_CLI"
    HTTP_REQUEST = "http_request"
    HTTP_RESPONSE = "http_response"
    REMOTE_LOGGER = "remote logger"
    SHELL_COMMAND = "shell command"
    STEP_LOGGER = "STEP"
    GATLING_RUNNER = "gatling runner"
    FIXTURE_LOGGER = "FIXTURE"
    FINALIZER_LOGGER = "FINALIZER"
