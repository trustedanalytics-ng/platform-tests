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

import os

from bson import ObjectId

from modules.constants import TapComponent as TAP
from tap_component_config import api_service, third_party_services


try:
    # In user_config.py, user might export custom environment variables
    import user_config
except ImportError:
    pass


def get_bool(key_name, fallback=None):
    value = os.environ.get(key_name, fallback)
    if value != fallback:
        value = value.lower()
        if value == "true":
            value = True
        elif value == "false":
            value = False
        else:
            raise ValueError("Value of {} env variable is '{}'. Should be 'True' or 'False'.".format(key_name, value))
    return value


def get_int(key_name, fallback=None):
    value = os.environ.get(key_name, fallback)
    if value != fallback:
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Value '{}' of {} env variable cannot be cast to int.".format(value, key_name))
    return value


def _delete_empty_env_variables():
    """
    Delete from os.environ items whose key starts with PT_ and whose values are empty.
    When tests are run on TeamCity, empty environment variables are set.
    """
    empty_variables = []
    for key_name, value in os.environ.items():
        if key_name.startswith("PT_") and value == "":
            empty_variables.append(key_name)
    for key_name in empty_variables:
        del os.environ[key_name]


def _assert_config_value_set(variable_name):
    attr = globals().get(variable_name)
    assert attr is not None, "Configuration variable '{}' not set.".format(variable_name)


"""
Retrieve configuration from environment variables or set to defaults.
NOTE: for all config items, respective env variable names should start with a 'PT_' prefix.
"""

_delete_empty_env_variables()

# configuration of TAP under test
tap_domain = os.environ["PT_TAP_DOMAIN"]
kerberos = get_bool("PT_KERBEROS", False)
kubernetes = get_bool("PT_KUBERNETES", True)
seahorse = get_bool("PT_SEAHORSE", False)
core_org_name = os.environ.get("PT_CORE_ORG_NAME", "default")
core_space_name = os.environ.get("PT_CORE_SPACE_NAME", "platform")
ssl_validation = get_bool("PT_SSL_VALIDATION", False)
tap_repos_dir = os.environ.get("PT_TAP_REPOS_DIRECTORY")

# TAP version provided by user
tap_version = os.environ.get("PT_TAP_VERSION")

# TAP infrastructure type provided by user (AWS, OS or Hybrid)
tap_infrastructure_type = os.environ.get("PT_TAP_INFRASTRUCTURE_TYPE")

# TAP build number (last number from version - 0.8.XXXX)
tap_build_number = get_int("PT_BUILD_NUMBER")

# local_appstack_path - if None, appstack is retrieved from GitHub apployer repository
appstack_file_path = os.environ.get("PT_APPSTACK_PATH")
appstack_version = os.environ.get("PT_APPSTACK_VERSION", "master")

# jumpbox configuration
jumpbox_hostname = os.environ.get("PT_JUMPBOX_HOSTNAME", "jump.{}".format(tap_domain))
jumpbox_username = os.environ.get("PT_JUMPBOX_USERNAME", "ubuntu")
jumpbox_key_path = os.environ.get("PT_JUMPBOX_KEY_PATH", os.path.expanduser(os.path.join("~", ".ssh", "auto-deploy-virginia.pem")))

# when TAP is behind a proxy, e.g. proxy-mu.intel.com
cf_proxy = os.environ.get("PT_CF_PROXY")

# Credentials - secrets are obligatory
admin_username = os.environ.get("PT_ADMIN_USERNAME", "taptester")  # Test user
admin_password = os.environ["PT_ADMIN_PASSWORD"]  # Secret
github_user_username = os.environ.get("PT_GITHUB_USER_USERNAME", "inteldatatests")
_github_user_password = os.environ.get("PT_GITHUB_USER_PASSWORD")  # Secret
arcadia_username = os.environ.get("PT_ARCADIA_USERNAME", "admin")
_arcadia_password = os.environ.get("PT_ARCADIA_PASSWORD")
cdh_manager_username = os.environ.get("PT_CDH_MANAGER_USERNAME", "admin")
_cdh_manager_password = os.environ.get("PT_CDH_MANAGER_PASSWORD")  # Secret
kinit_username = os.environ.get("PT_KINIT_USERNAME", "cf")
_kinit_password = os.environ.get("PT_KINIT_PASSWORD")  # Secret

# cdh
cdh_master_0_hostname = "cdh-master-0"
cdh_master_2_hostname = "cdh-master-2"
cdh_master_username = "ec2-user"
cdh_manager_port = 7180

# External SSL configuration:
external_protocol = os.environ.get("PT_EXTERNAL_PROTOCOL", "http")

# TAP services and urls - specify if other than xxx.<tap_domain>
# cf & uaa
cf_api_version = os.environ.get("PT_CF_API_VERSION", "v2")
cf_api_url = "api.{}".format(tap_domain)
cf_api_url_full = os.environ.get("PT_CF_API_URL", "{}://{}/{}".format(external_protocol, cf_api_url, cf_api_version))
cf_oauth_token_url = os.environ.get("PT_CF_OAUTH_TOKEN_URL", "https://login.{}/oauth/token".format(tap_domain))

uaa_url = os.environ.get("PT_UAA_URL", "{}://uaa.{}".format(external_protocol, tap_domain))
uaa_oauth_token_url = os.environ.get("PT_UAA_OAUTH_TOKEN_URL", "{}://uaa.{}/oauth/token".format(external_protocol, tap_domain))
console_login_url = os.environ.get("PT_CONSOLE_LOGIN_URL", "{}://uaa.{}".format(external_protocol, tap_domain))
auth_gateway_url = os.environ.get("PT_AUTH_GATEWAY_URL", "{}://auth-gateway.{}".format(external_protocol, tap_domain))
# TAP services
console_url = os.environ.get("PT_CONSOLE_URL", "{}://console.{}".format(external_protocol, tap_domain))
console_url_for_platform_tests_app = os.environ.get("PT_CONSOLE_URL_FOR_PLATFORM_TESTS_APP",
                                                    "{}://console.{}".format(external_protocol, tap_domain))
arcadia_url = os.environ.get("PT_ARCADIA_URL", "{}://arcadia.{}".format(external_protocol, tap_domain))
hue_url = os.environ.get("PT_HUE_URL", "{}://hue.{}".format(external_protocol, tap_domain))
demiurge_url = os.environ.get("PT_DEMIURGE_URL", "{}://demiurge.{}".format(external_protocol, tap_domain))
kubernetes_broker_url = os.environ.get("PT_KUBERNETES_BROKER_URL", "{}://kubernetes-broker.{}".format(external_protocol, tap_domain))
grafana_url = os.environ.get("PT_GRAFANA_URL", "{}://grafana.{}".format(external_protocol, tap_domain))

# Test resources
test_user_email = os.environ.get("PT_TEST_USER_EMAIL", "intel.data.tests@gmail.com")
database_url = os.environ.get("PT_DATABASE_URL")  # if specified, results will be logged in database
# This config value is only used by the platform-test app
test_run_id = os.environ.get("PT_TEST_RUN_ID")
data_repo_url = os.environ.get("PT_DATA_REPO_URL", None)

# Logsearch
collect_logsearch_logs = get_bool("PT_COLLECT_LOGSEARCH_LOGS", True)
logsearch_collect_retry_count = get_int("PT_LOGSEARCH_COLLECT_RETRY_COUNT", 5)

# Logging
logging_level = os.environ.get("PT_LOGGING_LEVEL", "DEBUG")
verbose_ssh = get_bool("PT_VERBOSE_SSH", False)
logged_response_body_length = os.environ.get("PT_LOGGED_RESPONSE_BODY_LENGTH", 1024)
log_username = os.environ.get("PT_LOG_USERNAME", False)

# -------------------------------------- TAP NG -------------------------------------- #

api_version = os.environ.get("PT_API_VERSION", api_service[TAP.api_service]["api_version"])
api_url = "api.{}".format(tap_domain)
api_url_full = os.environ.get("PT_API_URL", "{}://{}/api/{}".format(external_protocol, api_url, api_version))
ng_disable_environment_check = get_bool("PT_DISABLE_ENVIRONMENT_CHECK", False)
ng_jump_ip = os.environ.get("PT_NG_JUMP_IP", "jump.{}".format(tap_domain))  # required for running component tests on TAP NG
ng_jump_key_path = os.environ.get("PT_NG_JUMP_KEY_PATH")  # if not passed, key will be retrieved from GitHub
ng_jump_user_with_kubectl_config = os.environ.get("PT_NG_JUMP_USER_WITH_ACCESS_TO_KUBECTL_CONFIG", "tap-admin")
ng_jump_user = os.environ.get("PT_NG_JUMP_USER", "centos")
ng_kubernetes_api_host = os.environ.get("PT_KUBERNETES_API_HOST", "localhost")
ng_kubernetes_api_port = get_int("PT_KUBERNETES_API_PORT", 8080)
ng_socks_proxy_port = get_int("PT_SOCKS_PROXY_PORT", 5555)
ng_kubernetes_api_version = os.environ.get("PT_KUBERNETES_API_VERSION", api_service[TAP.api_service]["api_version"])
ng_service_http_scheme = os.environ.get("PT_SERVICE_HTTP_SCHEME", "http")
ng_k8s_service_auth_username = os.environ.get("PT_K8S_SERVICE_AUTH_USERNAME", "admin")
_ng_k8s_service_auth_password = os.environ.get("PT_K8S_SERVICE_AUTH_PASSWORD", "password")
ng_image_repository_url = os.environ.get("PT_NG_IMAGE_REPOSITORY_URL", third_party_services[TAP.image_repository]["url"])
ng_api_service_oauth_token_url = os.environ.get("PT_NG_AS_OAUTH_TOKEN_URL",
                                                "{}://{}.{}/{}".format(external_protocol, "api", tap_domain,
                                                                         "api/{}/login".format(ng_kubernetes_api_version)))
check_tap_cli_version = get_bool("PT_CHECK_TAP_CLI_VERSION", True)

# Set to True if kubectl and core services are not accessible from jumpbox, but from master-0
access_to_core_services_from_jump = get_bool("PT_ACCESS_TO_CORE_SERVICES_FROM_JUMP", False)
master_0_hostname = os.environ.get("PT_MASTER_0_HOSTNAME", "compute-master")

# --------------------------------- Performance tests -------------------------------- #

locust_file = os.environ.get("PT_LOCUST_FILE", None)
num_clients = get_int("PT_NUM_CLIENTS", 2)
hatch_rate = os.environ.get("PT_HATCH_RATE", "1")
test_duration = get_int("PT_DURATION", 10) * 60
locust_port = os.environ.get("PT_LOCUST_PORT", "8089")
locust_address = "http://localhost:{}".format(locust_port)
stress_run_id = os.environ.get("PT_STRESS_RUN_ID", None)
if stress_run_id:
    stress_run_id = ObjectId(stress_run_id)
log_metrics_interval = get_int("PT_LOG_METRICS_INTERVAL", 0)
log_requests = get_bool("PT_LOG_REQUESTS", False)
unique_id = os.environ.get("PT_UNIQUE_ID", None)
perf_user_names = os.environ.get("PT_PERF_USER_NAMES", "").split()
admin_username = os.environ.get("PT_PERF_ADMIN_USERNAME", admin_username)


def ng_k8s_service_credentials() -> tuple:
    _assert_config_value_set("_ng_k8s_service_auth_password")
    return ng_k8s_service_auth_username, _ng_k8s_service_auth_password


def github_credentials() -> tuple:
    # _github_user_password may be None, and this is ok in some scenarios
    return github_user_username, _github_user_password


def cdh_manager_credentials() -> tuple:
    _assert_config_value_set("_cdh_manager_password")
    return cdh_manager_username, _cdh_manager_password


def arcadia_credentials() -> tuple:
    _assert_config_value_set("_arcadia_password")
    return arcadia_username, _arcadia_password


def kinit_password():
    _assert_config_value_set("_kinit_password")
    return _kinit_password

