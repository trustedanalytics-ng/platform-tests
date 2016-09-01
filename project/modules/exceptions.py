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


class AtkScriptException(AssertionError):
    pass


class AtkTestException(AssertionError):
    pass


class UnexpectedResponseError(AssertionError):
    def __init__(self, status, error_message, message=None):
        message = message or "{} {}".format(status, error_message)
        super(UnexpectedResponseError, self).__init__(message)
        self.status = status
        self.error_message = error_message


class HdfsException(Exception):
    pass


class CommandExecutionException(Exception):
    """Local and remote (ssh)"""
    def __init__(self, return_code, output, command):
        super().__init__()
        self.return_code = return_code
        self.output = output
        self.command = command


class YouMustBeJokingException(Exception):
    pass


class JobException(Exception):
    pass


class RedirectionLimitException(Exception):
    pass


class NoSuchUserException(Exception):

    def __init__(self, message, *args, **kwargs):
        super().__init__("User: {} not exist".format(message), *args, **kwargs)


class ModelNotFoundException(Exception):
    pass
