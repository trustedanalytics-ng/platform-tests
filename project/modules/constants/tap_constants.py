#
# Copyright (c) 2017 Intel Corporation
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
    APPLICATION_ALREADY_EXISTS = "already exists"
    AUTHENTICATION_FAILED = "Authentication failed"
    AUTHENTICATION_SUCCEEDED = "Authentication succeeded"
    CHANGING_PASSWORD_FAILED = "Changing user password failed"
    CANNOT_BIND_UNBIND_INSTANCES_WITH_BOTH_DST_AND_SRC_FLAGS_SET = 'Cannot use more then one alternative flags' \
                                                                   ' (dst-name AND src-name) in the same time'
    CANNOT_DELETE_BOUND_SERVICE = 'Instance: {} is bound to other instance: {}, id: {}'
    CANNOT_DELETE_APPLICATION_IN_RUNNING_STATE = "event DESTROY_REQ inappropriate in current state RUNNING"
    CANNOT_FIND_APPLICATION_WITH_NAME = "Application {} not found"
    CANNOT_FIND_INSTANCE_WITH_NAME = "cannot find instance with name: {}"
    CANNOT_FIND_MANIFEST = "error: manifest.json does not exist: create one with metadata about your application"
    CANNOT_FIND_PLAN_FOR_SERVICE = "cannot find plan: '{}' for service: '{}'"
    CANNOT_FIND_SERVICE = "cannot find service: '{}'"
    CANNOT_REACH_API = "Cannot reach API. Not a TAP environment?"
    CANNOT_DELETE_RUNNING_APP = "event DESTROY_REQ inappropriate in current state RUNNING"
    CODE_CANNOT_DELETE_BOUND_SERVICE = 'CODE: 403 BODY: '
    CANNOT_DELETE_OFFERING_WITH_INSTANCE = "offering instance exists"
    INCORRECT_USAGE = "Incorrect Usage"
    INSTANCE_IS_BOUND_TO_OTHER_INSTANCE = "Instance: {} is bound to other instance: {}, id: {}"
    NO_SUCH_FILE_OR_DIRECTORY = "open {}: no such file or directory"
    MANIFEST_JSON_NO_SUCH_FILE = "manifest.json: no such file or directory"
    MANIFEST_JSON_INCORRECT_NAME_VALUE = "field: Name has incorrect value: {}"
    NO_SUCH_OFFERING = "Could not find offering with such name"
    MISSING_PARAMETER = "MISSING PARAMETER"
    NAME_HAS_INCORRECT_VALUE = "field: Name has incorrect value: {}"
    DOMAIN_NOT_FOUND = "Domain not found."
    OK = "OK"
    SERVICE_ALREADY_EXISTS = "service with name: {} already exists!"
    SUCCESS = "success"
    MSG_RESEND_NOT_EXIST_INVITATION = "Resending invitation to email {} failed error"


class TapApplicationType:
    GO = "GO"
    JAVA = "JAVA"
    NODEJS = "NODEJS"
    PYTHON27 = "PYTHON2.7"
    PYTHON34 = "PYTHON3.4"
