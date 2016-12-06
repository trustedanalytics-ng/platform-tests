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
    OFFLINE = "OFFLINE"
    PENDING = "PENDING"
    BUILDING = "BUILDING"
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
    AUTHENTICATION_FAILED = "Authentication failed"
    AUTHENTICATION_SUCCEEDED = "Authentication succeeded"
    CANNOT_DELETE_BOUND_SERVICE = 'Instance: {} is bound to other instance: {}, id: {}'
    CANNOT_FIND_INSTANCE_WITH_NAME = "cannot find instance with name: {}"
    CANNOT_FIND_PLAN_FOR_SERVICE = "cannot find plan: '{}' for service: '{}'"
    CANNOT_FIND_SERVICE = "cannot find service: '{}'"
    CANNOT_REACH_API = "Cannot reach API. Not a TAP environment?"
    CODE_CANNOT_DELETE_BOUND_SERVICE = 'CODE: 403 BODY: '
    INSTANCE_IS_BOUND_TO_OTHER_INSTANCE = "Instance: {} is bound to other instance: {}, id: {}"
    NO_SUCH_FILE_OR_DIRECTORY = "open {}: no such file or directory"
    NOT_ENOUGH_ARGS_CREATE_OFFERING = "not enough args: create-offering <path to json with service definition>"
    NOT_ENOUGH_ARGS_CREATE_SERVICE = "not enough args: create-service <service_name> <plan_name> <custom_name>"
    NOT_ENOUGH_ARGS_DELETE_SERVICE = "not enough args: delete-service <service_custom_name>"
    NO_SUCH_HOST = "no such host"
    OK = "OK"
    SERVICE_ALREADY_EXISTS = "service with name: {} already exists!"
    SUCCESS = "success"


class TapApplicationType:
    GO = "GO"
    JAVA = "JAVA"
    NODEJS = "NODEJS"
    PYTHON27 = "PYTHON2.7"
    PYTHON34 = "PYTHON3.4"
