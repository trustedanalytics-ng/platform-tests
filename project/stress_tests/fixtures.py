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
import logging
import os

import config
from modules.command import run
from modules.constants import ApplicationPath
from modules.mongo_reporter._tap_info import TapInfo
from modules.tap_object_model import User
from modules.tap_object_model.flows import onboarding
from modules.test_names import TapObjectName
from tests.fixtures.context import Context
from tests.fixtures.fixtures import core_org, test_data_urls

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CORE_ORG = core_org()
PERFORMANCE_CONTEXT = Context()


def build_sample_apps():
    logger.info('Building sample apps')
    for app_dir in [ApplicationPath.SAMPLE_JAVA_APP, ApplicationPath.SAMPLE_PYTHON_APP,
                    ApplicationPath.SAMPLE_GO_APP]:
        run(['./build.sh'], cwd=app_dir)


def create_users():
    logger.info('Create users')

    names = [TapObjectName(prefix='perf_user').as_email() for _ in range(config.num_clients)]
    for name in names:
        onboarding.onboard(context=PERFORMANCE_CONTEXT,
                           username=name,
                           password=config.admin_password,
                           org_guid=CORE_ORG.guid,
                           check_email=False)

    usernames_on_platform = (user.username for user in User.get_all_users(CORE_ORG.guid))
    assert set(names).issubset(set(usernames_on_platform)), 'Failed to create required number of users'

    os.environ['PT_PERF_USER_NAMES'] = ' '.join(names)


def push_data_repo():
    data_repo = test_data_urls(PERFORMANCE_CONTEXT)
    os.environ['PT_DATA_REPO_URL'] = data_repo.server_url


def retrieve_platform_version():
    logger.info("Retrieve platform version")
    os.environ["PT_BUILD_NUMBER"] = str(TapInfo.get_build_number())


def fixture_only_for(locustfile_names, fixture):
    if type(locustfile_names) == str:
        locustfile_names = list(locustfile_names.split())

    if any(locustfile for locustfile in locustfile_names if locustfile in config.locust_file):
        fixture()


def fixture_not_for(locustfile_names, fixture):
    if type(locustfile_names) == str:
        locustfile_names = list(locustfile_names.split())

    if not any(locustfile for locustfile in locustfile_names if locustfile in config.locust_file):
        fixture()


def setup():
    logger.info('Performance setup phase')

    fixture_only_for(['model_catalog', 'data_catalog'], push_data_repo)
    retrieve_platform_version()
    fixture_only_for('app_pushing', build_sample_apps)
    fixture_not_for('onboarding', create_users)


def teardown():
    PERFORMANCE_CONTEXT.cleanup()
