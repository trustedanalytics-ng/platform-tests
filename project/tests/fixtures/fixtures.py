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

import pytest

from configuration import config
from modules import app_sources
from modules.api_client import ConsoleClient
from modules.constants import CfEnvApp, HttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.http_calls import cloud_foundry as cf
from modules.tap_logger import get_logger
from modules.tap_object_model import Organization, Space, User
from modules.tap_object_model.flows import cleaner
from .test_data import TestData


logger = get_logger(__name__)


# TODO until unittest.TestCase subclassing is not removed, session-scoped fixtures write to global variables
# TODO logger in fixtures should have special format


@pytest.fixture(scope="session")
def test_org(request):
    logger.info("Create test organization")
    TestData.test_org = Organization.api_create()

    def fin():
        logger.info("Delete test organization")
        try:
            TestData.test_org.cf_api_delete()
        except UnexpectedResponseError as e:
            # TODO delete this when cleanups are more in order
            if e.status == HttpStatus.CODE_NOT_FOUND:
                pass
            else:
                raise
    request.addfinalizer(fin)

    return TestData.test_org


@pytest.fixture(scope="session", autouse=True)
def cleanup_everything(request):
    # TODO make cleanup more precise: orgs with updated names, main test org, user, etc.
    def fin():
        cleaner.tear_down_all()
    request.addfinalizer(fin)


@pytest.fixture(scope="session")
def test_space(request, test_org):
    logger.info("Create test space")
    TestData.test_space = Space.api_create(test_org)
    return TestData.test_space


@pytest.fixture(scope="session")
def test_org_manager(request, test_org):
    logger.info("Add org manager to test org")
    TestData.test_org_manager = User.api_create_by_adding_to_organization(org_guid=test_org.guid)

    def fin():
        logger.info("Delete test org manager")
        TestData.test_org_manager.cf_api_delete()
    request.addfinalizer(fin)

    return TestData.test_org_manager


@pytest.fixture(scope="session")
def test_org_manager_client(test_org_manager):
    TestData.test_org_manager_client = test_org_manager.login()
    return TestData.test_org_manager_client


@pytest.fixture(scope="session")
def example_app_path():
    logger.info("Clone example application")
    sources = app_sources.AppSources(repo_name=CfEnvApp.repo_name, repo_owner=CfEnvApp.repo_owner)
    TestData.example_app_repo_path = sources.clone_or_pull()
    sources.checkout_commit(commit_id=CfEnvApp.commit_id)
    return TestData.example_app_repo_path


@pytest.fixture(scope="class")
def login_to_cf(test_org, test_space):
    logger.info("Login to cf targeting test org and test space")
    cf.cf_login(test_org.name, test_space.name)


@pytest.fixture(scope="session")
def admin_user():
    TestData.admin = User.get_admin()
    return TestData.admin


@pytest.fixture(scope="session")
def admin_client():
    TestData.admin_client = ConsoleClient.get_admin_client()
    return TestData.admin_client


@pytest.fixture(scope="session")
def add_admin_to_test_org(test_org, admin_user):
    admin_user.api_add_to_organization(org_guid=test_org.guid)


@pytest.fixture(scope="session")
def core_org():
    ref_org_name = config.CONFIG["ref_org_name"]
    orgs = Organization.cf_api_get_list()
    TestData.core_org = next(o for o in orgs if o.name == ref_org_name)
    return TestData.core_org


@pytest.fixture(scope="session")
def core_space():
    ref_space_name = config.CONFIG["ref_space_name"]
    spaces = Space.cf_api_get_list()
    TestData.core_space = next(s for s in spaces if s.name == ref_space_name)
    return TestData.core_space
