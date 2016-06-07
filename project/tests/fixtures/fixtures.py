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

import base64
import os
import io

import pytest

from retry import retry

from configuration import config
from modules.constants import HttpStatus, ApplicationPath
from modules.exceptions import UnexpectedResponseError
from modules.http_calls import cloud_foundry as cf
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.tap_logger import log_fixture, log_finalizer
from modules.tap_object_model import Organization, ServiceType, Space, User, Application
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
def test_sample_app(request, test_org, test_space):
    log_fixture("test_sample_app: Login to cf targeting test org and test space")
    cf.cf_login(test_org.name, test_space.name)
    log_fixture("test_sample_app: Push app to cf")
    app = Application.push(
        space_guid=test_space.guid,
        source_directory=ApplicationPath.SAMPLE_APP
    )

    def fin():
        log_fixture("test_sample_app: Delete sample app")
        app.api_delete()

    request.addfinalizer(fin)

    return app


@pytest.fixture(scope="session")
def test_sample_service(request, test_org, test_space, test_sample_app):
    log_fixture("test_sample_service: Register sample app in marketplace")
    service = ServiceType.register_app_in_marketplace(app_name=test_sample_app.name, app_guid=test_sample_app.guid,
                                                      org_guid=test_org.guid, space_guid=test_space.guid)
    log_fixture("test_sample_service: Get service plans")
    service.api_get_service_plans()

    def fin():
        log_fixture("test_sample_service: Delete service")
        service.api_delete()

    request.addfinalizer(fin)

    return service


@pytest.fixture(scope="session")
def admin_user():
    log_fixture("admin_user: Retrieve admin user")
    admin_user = User.get_admin()
    TestData.admin_user = admin_user
    return admin_user


@pytest.fixture(scope="session")
def admin_client():
    log_fixture("admin_client: Get http client for admin")
    TestData.admin_client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return TestData.admin_client


@pytest.fixture(scope="session")
def space_users_clients(request, test_org, test_space, admin_client):
    context = Context()
    log_fixture("clients: Create clients")
    _clients = {}
    for role, value in User.SPACE_ROLES.items():
        _clients[role] = User.api_create_by_adding_to_space(context, org_guid=test_org.guid, space_guid=test_space.guid,
                                                            roles=value).login()
    _clients["admin"] = admin_client

    def fin():
        log_finalizer("clients: Delete test users")
        context.cleanup()

    request.addfinalizer(fin)
    return _clients


@pytest.fixture(scope="session")
def add_admin_to_test_org(test_org, admin_user):
    log_fixture("add_admin_to_test_org")
    admin_user.api_add_to_organization(org_guid=test_org.guid)


@pytest.fixture(scope="session")
def add_admin_to_test_space(test_org, test_space, admin_user):
    log_fixture("add_admin_to_test_space")
    admin_user.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid, roles=User.SPACE_ROLES["developer"])


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


@pytest.fixture(scope="session")
def test_marketplace(test_space):
    log_finalizer("test_marketplace: Get list of marketplace services in test space")
    return ServiceType.api_get_list_from_marketplace(space_guid=test_space.guid)


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


@pytest.fixture
def example_image():
    file_path = os.path.join("fixtures", "example_image.png")
    content64 = io.BytesIO()
    content64.write(bytes("data:image/png;base64,", "utf8"))
    base64.encode(open(file_path, "rb"), content64)
    return content64.getvalue()
