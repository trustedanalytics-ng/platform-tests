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


class TapEntityState:
    DEPLOYING = "DEPLOYING"
    DESTROY_REQ = "DESTROY_REQ"
    DESTROYING = "DESTROYING"
    FAILURE = "FAILURE"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    READY = "READY"
    REQUESTED = "REQUESTED"
    RUNNING = "RUNNING"
    START_REQ = "START_REQ"
    STARTING = "STARTING"
    STOP_REQ = "STOP_REQ"
    STOPPED = "STOPPED"
    STOPPING = "STOPPING"
    UNAVAILABLE = "UNAVAILABLE"


class TapMessage:
    CANNOT_FIND_INSTANCE_WITH_NAME = "cannot find instance with name: {}"
    MSG_CANNOT_DELETE_BOUND_SERVICE = 'Instance: {} is bound to other instance: {}, id: {}'
    CODE_CANNOT_DELETE_BOUND_SERVICE = 'CODE: 403 BODY: '
    AUTHENTICATION_FAILED = "Authentication failed"
    AUTHENTICATION_SUCCEEDED = "Authentication succeeded"
    NO_SUCH_HOST = "no such host"


class TapApplicationType:
    GO = "GO"
    JAVA = "JAVA"
    NODEJS = "NODEJS"
    PYTHON27 = "PYTHON2.7"
    PYTHON34 = "PYTHON3.4"
