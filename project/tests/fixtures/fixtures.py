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
from retry import retry

from configuration import config
from modules.api_client import ConsoleClient
from modules.constants import HttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.http_calls import cloud_foundry as cf
from modules.tap_logger import log_fixture, log_finalizer
from modules.tap_object_model import DataSet, Invitation, Organization, Space, Transfer, User
from modules.test_names import is_test_object_name
from .context import Context
from .test_data import TestData



# TODO until unittest.TestCase subclassing is not removed, session-scoped fixtures write to global variables
# TODO logger in fixtures should have special format


@pytest.fixture(scope="session")
@retry(UnexpectedResponseError, tries=3, delay=15)
def test_org(request):
    context = Context()
    log_fixture("test_org: Create test organization")
    test_org = Organization.api_create(context)
    TestData.test_org = test_org

    def fin():
        log_finalizer("test_org: Delete test organization")
        context.cleanup()
    request.addfinalizer(fin)

    return test_org


@pytest.fixture(scope="session")
def test_space(request, test_org):
    log_fixture("test_space: Create test space")
    TestData.test_space = Space.api_create(test_org)
    return TestData.test_space


@pytest.fixture(scope="session")
def test_org_manager(request, test_org):
    context = Context()
    log_fixture("test_org_manager: Add org manager to test org")
    test_org_manager = User.api_create_by_adding_to_organization(context, org_guid=test_org.guid)
    TestData.test_org_manager = test_org_manager
    def fin():
        log_finalizer("test_org_manager: Delete test org manager")
        context.cleanup()
    request.addfinalizer(fin)
    return test_org_manager


@pytest.fixture(scope="session")
def test_org_manager_client(test_org_manager):
    log_fixture("test_org_manager_client: Login as test org manager")
    TestData.test_org_manager_client = test_org_manager.login()
    return TestData.test_org_manager_client


@pytest.fixture(scope="class")
def login_to_cf(test_org, test_space):
    log_fixture("login_to_cf: Login to cf targeting test org and test space")
    cf.cf_login(test_org.name, test_space.name)


@pytest.fixture(scope="session")
def admin_user():
    log_fixture("admin_user: Retrieve admin user")
    admin_user = User.get_admin()
    TestData.admin_user = admin_user
    return admin_user


@pytest.fixture(scope="session")
def admin_client():
    log_fixture("admin_client: Get http client for admin")
    TestData.admin_client = ConsoleClient.get_admin_client()
    return TestData.admin_client


@pytest.fixture(scope="session")
def add_admin_to_test_org(test_org, admin_user):
    log_fixture("add_admin_to_test_org")
    admin_user.api_add_to_organization(org_guid=test_org.guid)


@pytest.fixture(scope="session")
def core_org():
    log_fixture("core_org: Create object for core org")
    ref_org_name = config.CONFIG["ref_org_name"]
    orgs = Organization.cf_api_get_list()
    TestData.core_org = next(o for o in orgs if o.name == ref_org_name)
    return TestData.core_org


@pytest.fixture(scope="session")
def core_space():
    log_fixture("core_space: Create object for core space")
    ref_space_name = config.CONFIG["ref_space_name"]
    spaces = Space.cf_api_get_list()
    TestData.core_space = next(s for s in spaces if s.name == ref_space_name)
    return TestData.core_space


def log_objects(object_list, object_type_name):
    # TODO delete - this is temporary, for validation purposes
    if len(object_list) == 0:
        log_finalizer("No {}s to delete".format(object_type_name))
    else:
        log_finalizer("Remaining {} {}{}:\n{}".format(len(object_list), object_type_name,
                                                      "s" if len(object_list) != 1 else "",
                                                      "\n".join([str(x) for x in object_list])))


def get_objects_and_log():
    # TODO delete - this is temporary, for validation purposes
    log_finalizer("logging remaining objects")
    all_data_sets = DataSet.api_get_list()
    test_data_sets = [x for x in all_data_sets if is_test_object_name(x.title)]
    log_objects(test_data_sets, "data set")
    all_transfers = Transfer.api_get_list()
    test_transfers = [x for x in all_transfers if is_test_object_name(x.title)]
    log_objects(test_transfers, "transfer")
    all_users = User.cf_api_get_all_users()
    test_users = [x for x in all_users if is_test_object_name(x.username)]
    log_objects(test_users, "user")
    all_pending_invitations = Invitation.api_get_list()
    test_invitations = [x for x in all_pending_invitations if is_test_object_name(x.username)]
    log_objects(test_invitations, "invitation")
    all_orgs = Organization.cf_api_get_list()
    test_orgs = [x for x in all_orgs if is_test_object_name(x.name)]
    log_objects(test_orgs, "org")


@pytest.fixture(scope="class", autouse=True)
def log_remaining_objects_class(request):
    # TODO delete - this is temporary, for validation purposes
    try:
        request.addfinalizer(lambda: get_objects_and_log())
    except:
        pass


@pytest.fixture(scope="session", autouse=True)
def log_remaining_objects_session(request):
    # TODO delete - this is temporary, for validation purposes
    try:
        request.addfinalizer(lambda: get_objects_and_log())
    except:
        pass


def delete_or_not_found(delete_method, *args, **kwargs):
    try:
        delete_method(*args, **kwargs)
    except UnexpectedResponseError as e:
        if e.status != HttpStatus.CODE_NOT_FOUND:
            raise


def tear_down_test_objects(object_list: list):
    for item in object_list:
        try:
            item.cleanup()
        except UnexpectedResponseError as e:
            log_finalizer("Error while deleting {}: {}".format(item, e))
