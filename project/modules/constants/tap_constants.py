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


class TapCliState:
    REQUESTED = "REQUESTED"
    DEPLOYING = "DEPLOYING"
    FAILURE = "FAILURE"
    STOPPED = "STOPPED"
    START_REQ = "START_REQ"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOP_REQ = "STOP_REQ"
    STOPPING = "STOPPING"
    DESTROY_REQ = "DESTROY_REQ"
    DESTROYING = "DESTROYING"
    UNAVAILABLE = "UNAVAILABLE"


class TapCliResponse:
    CANNOT_FIND_INSTANCE_WITH_NAME = "cannot find instance with name: {}"
    MSG_CANNOT_DELETE_BOUND_SERVICE = 'Instance: {} is bound to other instance: {}, id: {}'
    CODE_CANNOT_DELETE_BOUND_SERVICE = 'CODE: 403 BODY: '
