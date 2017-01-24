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
    CODE_TOO_MANY_REQUESTS = 429

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

    MSG_GUID_CODE_IS_INVALID_EXCEPTION = "Guid code is invalid."
    MSG_EMAIL_ADDRESS_NOT_VALID = "That email address is not valid"
    MSG_MUST_HAVE_AT_LEAST_ONE_ROLE = "You must have at least one role"
    MSG_CANNOT_PERFORM_REQ_WITHOUT_ROLES = "You cannot perform request without specified roles"
    MSG_CANNOT_PERFORM_REQ_ON_YOURSELF = "You cannot perform request on yourself."
    MSG_USER_NOT_EXIST_IN_ORGANIZATION = "User {} does not exist in organization {}."
    MSG_USER_ALREADY_EXISTS = "User {} already exists"
    MSG_USER_NOT_EXIST = "The user does not exist"
    MSG_ACCESS_IS_DENIED = "Access is denied"
    MSG_ACCESS_DENIED = "access_denied"
    MSG_INCORRECT_PASSWORD = "forgot_password"
    MSG_PASSWORD_CANNOT_BE_EMPTY = "Password cannot be empty"
    MSG_ORGANIZATION_ALREADY_EXISTS = "Organization \\\"{}\\\" already exists"
    MSG_ORGANIZATION_ALREADY_TAKEN = "The organization name is taken: {}"
    MSG_NO_PENDING_INVITATION_FOR = "No pending invitation for {}"
    MSG_ORGANIZATION_CANNOT_CONTAIN_ONLY_WHITESPACES = "Organization cannot contain only whitespace characters"


class DataCatalogHttpStatus(HttpStatus):
    """Data catalog http status messages"""

    MSG_NOT_VALID_UUID = "You do not have access to requested organization"
    MSG_INVALID_REQUEST = "Invalid request"


class ServiceCatalogHttpStatus(HttpStatus):
    """Services http status messages"""

    MSG_SERVICE_NAME_TAKEN = "Provided name {} is already in use by other instance."
    MSG_BOUND_INSTANCE = "Instance: {} is bound to other instance: {}, id: {}"
    MSG_APP_NOT_FOUND = "cannot fetch instance of application with id {}"
    MSG_CANNOT_BOUND_INSTANCE = "Cannot bind instance {} to {}"
    MSG_SERVICE_BINDING_NOT_FOUND = "The service binding could not be found: {}"
    MSG_NOT_AUTHORIZED = "You are not authorized"
    MSG_USER_NOT_AUTHORIZED_TO_DELETE_SERVICE = "User not authorize to delete this service"
    MSG_CANNOT_REMOVE_SERVICE_WITH_INSTANCE = "There is an instance of service being deleted"
    MSG_SERVICE_EXISTS = "service with name: {} already exists!"
    MSG_SERVICE_DOES_NOT_EXIST = "100: Key not found"
    MSG_SERVICE_NAME_IS_EMPTY = "Service name should not be empty"
    MSG_ACCESS_FORBIDDEN = "Access Forbidden"


class KubernetesBrokerHttpStatus(HttpStatus):
    MSG_SECRET_NOT_FOUND = "secrets \"{}\" not found"
    MSG_SECRET_ALREADY_EXISTS = "secrets \"{}\" already exists"
    MSG_INVALID_SECRET = "Secret \"{}\" is invalid"


class PlatformTestsHttpStatus(HttpStatus):
    MSG_RUNNER_BUSY = "Runner is busy"


class ImageFactoryHttpStatus(HttpStatus):
    MSG_BLOB_ID_ALREADY_IN_USE = "The specified Blob ID is already in use"
    MSG_BLOB_DOES_NOT_EXIST = "The specified blob does not exist"
    MSG_CREATE_IMAGE_WITH_INVALID_BODY = "json: cannot unmarshal string into Go value of type " \
                                         "models.BuildImagePostRequest"


class BlobStoreHttpStatus(HttpStatus):
    MSG_BLOB_ID_ALREADY_IN_USE = "The specified Blob ID is already in use"
    MSG_BLOB_DOES_NOT_EXIST = "The specified blob does not exist"
    MSG_BLOB_CONTENT_MISSING = "Blob not specified."
    MSG_BLOB_ID_MISSING = "The blobID is not specified."


class TemplateRepositoryHttpStatus(HttpStatus):
    MSG_TOO_SHORT_INSTANCE_ID = "instanceId has to be longer than 15 characters!"
    MSG_TEMPLATE_DOES_NOT_EXIST = "template doesn't exist!"
    MSG_NO_TEMPLATE = "there is no template \\\"{}\\\""
    MSG_UUID_CANNOT_BE_EMPTY = "uuid can't be empty!"
    MSG_CANT_FIND_TEMPLATE = "can't find template by id: {}"
    MSG_REMOVE_TEMPLATE_FORBIDDEN = "removing template {} is forbidden"
    MSG_TEMPLATE_EXISTS = "Template with Id: {} already exists!"


class CatalogHttpStatus(HttpStatus):
    MSG_TOO_SHORT_SERVICE_ID = "serviceId has to be longer than 15 characters!"
    MSG_INSTANCE_FORBIDDEN_CHARACTERS = "Field: Name has incorrect value: {}"
    MSG_INVALID_JSON = "unexpected end of JSON input"
    MSG_INSTANCE_UNCHANGED_FIELDS = "ID and Name fields can not be changed!"
    MSG_KEY_NOT_FOUND = "100: Key not found"
    MSG_KEY_PLAN_ID_NOT_FOUND = "key PLAN_ID not found!"
    MSG_SERVICE_EXISTS = "service with name: {} already exists!"
    MSG_APPLICATION_EXISTS = "application \\\"{}\\\" already exists"
    MSG_INSTANCE_EXISTS = "instance with name: {} already exists!"
    MSG_ID_HAS_TO_BE_EMPTY = "Id field has to be empty!"
    MSG_OFFERING_SHOULD_HAVE_PLAN = "offering should have at least one plan"
    MSG_EVENT_DOES_NOT_EXIST = "event {} does not exist"
    MSG_COMPARE_FAILED = "101: Compare failed ([\\\"{}\\\" != \\\"{}\\\"]"
    MSG_COMPARE_FAILED_NO_QUOTES = "101: Compare failed ([{} != {}]"
    MSG_FIELD_IS_EMPTY = "field {} is empty!"
    MSG_KEY_EXISTS = "Key already exists"
    MSG_INCORRECT_TYPE = "json: cannot unmarshal string into Go value of type int"
    MSG_APP_FORBIDDEN_CHARACTERS = "field Name has incorrect value: {}"
    MSG_SERVICE_DOES_NOT_EXIST = "service with id: {} does not exists!"
    MSG_APPLICATION_DOES_NOT_EXIST = "application with id: {} does not exists!"
    MSG_CLASS_ID_CANNOT_BE_CHANGED = "ClassID fields can not be changed!"


class ApiServiceHttpStatus(HttpStatus):
    MSG_SERVICE_ALREADY_EXISTS = "service with name: {} already exists!"
    MSG_SERVICE_INSTANCE_ALREADY_EXISTS = "instance with name: {} already exists!"
    MSG_KEY_NOT_FOUND = "Key not found"
    MSG_CANNOT_FETCH_INSTANCE = "Cannot fetch instance {} from Catalog"
    MSG_CANNOT_FETCH_APP_INSTANCE = "cannot fetch instance of application with id {} from Catalog"
    MSG_INCORRECT_TYPE = "json: cannot unmarshal string into Go value of type int"
    MSG_BAD_REQUEST = "Bad response status"
    MSG_FIELD_INCORRECT_VALUE = "Field: {} has incorrect value"
    MSG_FIELD_ZERO_VALUE = "{}: zero value"
    MSG_PLAN_CANNOT_BE_FOUND = "plan with id \\\"{}\\\" does not exist in offering"
    MSG_MINIMUM_ALLOWED_REPLICA = "Replicas: less than min"


class ContainerBrokerHttpStatus(HttpStatus):
    MSG_SERVICES_NOT_FOUND = "service instance {} is not found"
    MSG_CONFIGMAPS_NOT_FOUND = "configmaps \\\"{}\\\" not found"
    MSG_SECRET_NOT_FOUND = "secrets \\\"{}\\\" not found"
    MSG_CANNOT_EXPOSE = "can not expose instance: {}. Ports must match service ports. " \
                        "Port: {} does not exist in Service!"
    MSG_EMPTY_HOSTNAME = "Ingress.extensions \\\"{}\\\" is invalid: spec.rules[0].host: Invalid value: " \
                         "\\\"{}\\\": must match the regex " \
                         "[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)* (e.g. 'example.com')"
    MSG_INGRESS_ALREADY_EXISTS = "ingresses.extensions \\\"{}\\\" already exists"
    MSG_INGRESS_NOT_FOUND = "ingresses.extensions \\\"{}\\\" not found"


class ModelCatalogHttpStatus(HttpStatus):
    MSG_MODEL_NOT_FOUND = "Model with given {} not found"
    MSG_INVALID_UUID = "Invalid UUID string: {}"
    MSG_MISSING_PARAM = "Non-empty value is required for model {} field"
