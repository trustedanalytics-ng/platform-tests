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

import os

import pytest
import requests
from teamcity import is_running_under_teamcity

from configuration import config
from modules.constants import Path
from modules.tap_logger import get_logger, change_log_file_path


logger = get_logger(__name__)


def check_environment_viability():
    """Check that basic calls to the console and cf api work"""
    try:
        domain = config.CONFIG["domain"]
        verify = config.CONFIG["ssl_validation"]
        console_endpoint = "https://console.{}".format(domain)
        cf_endpoint = "https://api.{}/{}/info".format(domain, config.CONFIG["cf_api_version"])
        requests.get(console_endpoint, verify=verify).raise_for_status()
        requests.get(cf_endpoint, verify=verify).raise_for_status()
    except requests.HTTPError as e:
        logger.error("Environment {} is unavailable - status {}".format(e.response.url, e.response.status_code))
        raise


if __name__ == "__main__":

    # parse settings passed from command line and update config
    args = config.parse_arguments()

    if not is_running_under_teamcity():
        log_dir = args.log_file_directory
        os.makedirs(log_dir, exist_ok=True)
        change_log_file_path(args.log_file_directory)

    config.update_test_config(client_type=args.client_type,
                              domain=args.environment,
                              logged_response_body_length=args.logged_response_body_length,
                              logging_level=args.logging_level,
                              platform_version=args.platform_version,
                              repository=args.repository,
                              database_url=args.database_url,
                              test_suite=args.suite,
                              local_appstack=args.local_appstack,
                              admin_password=args.admin_password,
                              admin_username=args.admin_username,
                              ref_org_name=args.reference_org,
                              ref_space_name=args.reference_space,
                              test_run_id=args.test_run_id,
                              disable_remote_logger=args.disable_remote_logger,
                              remote_logger_retry_count=args.remote_logger_retry_count,
                              kerberos=args.kerberos,
                              jumpbox_address=args.jumpbox_address,
                              elasticsearch_host=args.elasticsearch_host,
                              pushed_app_proxy=args.pushed_app_proxy,
                              kubernetes=args.kubernetes)

    for key in config.LOGGED_CONFIG_KEYS:
        logger.info("{}={}".format(key, config.CONFIG.get(key)))

    # check that environment is up and running
    check_environment_viability()

    suite_path = Path.test_root_directory
    if args.suite is not None:
        suite_path = os.path.join(suite_path, args.suite)
    pytest_options = [suite_path, "-s"]

    # TODO this tag parsing should be removed - to do this, need to change run_tests options api
    def join_tags(tag_list, positive=True):
        join_str = " or "
        if not positive:
            join_str = " and "
            tag_list = ["not " + tag for tag in tag_list]
        return "({})".format(join_str.join(tag_list))

    tags = []
    for tag_list in [args.priority, args.components, args.only_tagged]:
        if len(tag_list) > 0:
            tags.append(join_tags(tag_list))
    if len(args.not_tagged) > 0:
        tags.append(join_tags(args.not_tagged, positive=False))

    if len(tags) > 0:
        pytest_options += ["-m", " and ".join(tags)]

    if args.tests:
        pytest_options.extend([
            "-k",
            " or ".join(args.tests)
        ])

    logger.info("pytest_options: %s", pytest_options)

    pytest.main(pytest_options)
