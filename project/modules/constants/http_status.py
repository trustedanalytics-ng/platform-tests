#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License")
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


class HttpStatus(object):
    """Base http status codes and messages"""

    MSG_EMPTY = ""

    # --- 1xx Informational ---

    MSG_CONTINUE = "Continue"
    CODE_CONTINUE = 100
    MSG_SWITCHING_PROTOCOLS = "Switching Protocols"
    CODE_SWITCHING_PROTOCOLS = 101
    MSG_PROCESSING = "Processing"
    CODE_PROCESSING = 102

    # --- 2xx Success ---

    MSG_OK = "OK"
    CODE_OK = 200
    MSG_CREATED = "Created"
    CODE_CREATED = 201
    MSG_ACCEPTED = "Accepted"
    CODE_ACCEPTED = 202
    MSG_NON_AUTHORITATIVE_INFORMATION = "Non Authoritative Information"
    CODE_NON_AUTHORITATIVE_INFORMATION = 203
    MSG_NO_CONTENT = "No Content"
    CODE_NO_CONTENT = 204
    MSG_RESET_CONTENT = "Reset Content"
    CODE_RESET_CONTENT = 205
    MSG_PARTIAL_CONTENT = "Partial Content"
    CODE_PARTIAL_CONTENT = 206
    MSG_MULTI_STATUS = "Multi-Status"
    CODE_MULTI_STATUS = 207

    # --- 3xx Redirection ---

    MSG_MULTIPLE_CHOICES = "Multiple Choices"
    CODE_MULTIPLE_CHOICES = 300
    MSG_MOVED_PERMANENTLY = "Moved Permanently"
    CODE_MOVED_PERMANENTLY = 301
    MSG_MOVED_TEMPORARILY = "Moved Temporarily"
    CODE_MOVED_TEMPORARILY = 302
    MSG_SEE_OTHER = "See Other"
    CODE_SEE_OTHER = 303
    MSG_NOT_MODIFIED = "Not Modified"
    CODE_NOT_MODIFIED = 304
    MSG_USE_PROXY = "Use Proxy"
    CODE_USE_PROXY = 305
    MSG_TEMPORARY_REDIRECT = "Temporary Redirect"
    CODE_TEMPORARY_REDIRECT = 307

    # --- 4xx Client Error ---

    MSG_BAD_REQUEST = "Bad Request"
    CODE_BAD_REQUEST = 400
    MSG_UNAUTHORIZED = "Unauthorized"
    CODE_UNAUTHORIZED = 401
    MSG_PAYMENT_REQUIRED = "Payment Required"
    CODE_PAYMENT_REQUIRED = 402
    MSG_FORBIDDEN = "Forbidden"
    CODE_FORBIDDEN = 403
    MSG_NOT_FOUND = "Not Found"
    CODE_NOT_FOUND = 404
    MSG_METHOD_NOT_ALLOWED = "Method Not Allowed"
    MSG_METHOD_NOT_SUPPORTED = "Request method '{}' not supported"
    CODE_METHOD_NOT_ALLOWED = 405
    MSG_NOT_ACCEPTABLE = "Not Acceptable"
    CODE_NOT_ACCEPTABLE = 406
    MSG_PROXY_AUTHENTICATION_REQUIRED = "Proxy Authentication Required"
    CODE_PROXY_AUTHENTICATION_REQUIRED = 407
    MSG_REQUEST_TIMEOUT = "Request Timeout"
    CODE_REQUEST_TIMEOUT = 408
    MSG_CONFLICT = "Conflict"
    CODE_CONFLICT = 409
    MSG_GONE = "Gone"
    CODE_GONE = 410
    MSG_LENGTH_REQUIRED = "Length Required"
    CODE_LENGTH_REQUIRED = 411
    MSG_PRECONDITION_FAILED = "Precondition Failed"
    CODE_PRECONDITION_FAILED = 412
    MSG_REQUEST_TOO_LONG = "Request Entity Too Large"
    CODE_REQUEST_TOO_LONG = 413
    MSG_REQUEST_URI_TOO_LONG = "Request-URI Too Long"
    CODE_REQUEST_URI_TOO_LONG = 414
    MSG_UNSUPPORTED_MEDIA_TYPE = "Unsupported Media Type"
    CODE_UNSUPPORTED_MEDIA_TYPE = 415
    MSG_REQUESTED_RANGE_NOT_SATISFIABLE = "Requested Range Not Satisfiable"
    CODE_REQUESTED_RANGE_NOT_SATISFIABLE = 416
    MSG_EXPECTATION_FAILED = "Expectation Failed"
    CODE_EXPECTATION_FAILED = 417
    MSG_INSUFFICIENT_SPACE_ON_RESOURCE = "Insufficient Space on Resource"
    CODE_INSUFFICIENT_SPACE_ON_RESOURCE = 419
    MSG_METHOD_FAILURE = "Method Failure"
    CODE_METHOD_FAILURE = 420
    MSG_UNPROCESSABLE_ENTITY = "Unprocessable Entity"
    CODE_UNPROCESSABLE_ENTITY = 422
    MSG_LOCKED = "Locked"
    CODE_LOCKED = 423
    MSG_FAILED_DEPENDENCY = "Failed Dependency"
    CODE_FAILED_DEPENDENCY = 424

    # --- 5xx Server Error ---

    MSG_INTERNAL_SERVER_ERROR = "Internal Server Error"
    CODE_INTERNAL_SERVER_ERROR = 500
    MSG_NOT_IMPLEMENTED = "Not Implemented"
    CODE_NOT_IMPLEMENTED = 501
    MSG_BAD_GATEWAY = "Bad Gateway"
    CODE_BAD_GATEWAY = 502
    MSG_SERVICE_UNAVAILABLE = "Service Unavailable"
    CODE_SERVICE_UNAVAILABLE = 503
    MSG_GATEWAY_TIMEOUT = "Gateway Timeout"
    CODE_GATEWAY_TIMEOUT = 504
    MSG_HTTP_VERSION_NOT_SUPPORTED = "HTTP Version Not Supported"
    CODE_HTTP_VERSION_NOT_SUPPORTED = 505
    MSG_INSUFFICIENT_STORAGE = "Insufficient Storage"
    CODE_INSUFFICIENT_STORAGE = 507


class UserManagementHttpStatus(HttpStatus):
    """User management http status messages"""

    MSG_WRONG_UUID_FORMAT_EXCEPTION = "Wrong uuid format exception"
    MSG_EMAIL_ADDRESS_NOT_VALID = "That email address is not valid"
    MSG_MUST_HAVE_AT_LEAST_ONE_ROLE = "You must have at least one role"
    MSG_CANNOT_PERFORM_REQ_WITHOUT_ROLES = "You cannot perform request without specified roles"
    MSG_USER_NOT_EXIST_IN_ORGANIZATION = "User {} does not exist in organization {}."
    MSG_USER_ALREADY_EXISTS = "User {} already exists"
    MSG_USER_IS_NOT_IN_GIVEN_SPACE = "The user is not in given space"
    MSG_ACCESS_DENIED = "Access is denied"
    MSG_PASSWORD_CANNOT_BE_EMPTY = "Password cannot be empty"
    MSG_ORGANIZATION_ALREADY_EXISTS = "Organization \\\"{}\\\" already exists"
    MSG_ORGANIZATION_ALREADY_TAKEN = "Organization name already taken"
    MSG_NO_PENDING_INVITATION_FOR = "No pending invitation for {}"
    MSG_ORGANIZATION_CANNOT_CONTAIN_ONLY_WHITESPACES = "Organization cannot contain only whitespace characters"


class DataCatalogHttpStatus(HttpStatus):
    """Data catalog http status messages"""

    MSG_NOT_VALID_UUID = "not a valid UUID"
    MSG_INVALID_REQUEST = "Invalid request"


class ServiceCatalogHttpStatus(HttpStatus):
    """Services http status messages"""

    MSG_SERVICE_NAME_TAKEN = "Provided name {} is already in use by other instance."
    MSG_BOUND_INSTANCE = "Please delete the service_bindings, service_keys, and routes associations for your service_instances."
    MSG_APP_NOT_FOUND = "The app could not be found: {}"
    MSG_SERVICE_INST_NOT_FOUND = "The service instance could not be found: {}"
    MSG_SERVICE_BINDING_NOT_FOUND = "The service binding could not be found: {}"
