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

import config
from modules.app_sources import AppSources
from modules.constants import ApplicationPath, HttpStatus, ServiceLabels, TapGitHub, Urls
from modules.exceptions import UnexpectedResponseError
from modules.http_calls import cloud_foundry as cf
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.tap_logger import log_fixture, log_finalizer
from modules.tap_object_model import Application, Organization, ServiceType, ServiceInstance, Space, User
from modules.tap_object_model.flows import data_catalog
from .test_data import TestData




# TODO until unittest.TestCase subclassing is not removed, session-scoped fixtures write to global variables
# TODO logger in fixtures should have special format


@pytest.fixture(scope="session")
@retry(UnexpectedResponseError, tries=3, delay=15)
def test_org(request, session_context):
    log_fixture("test_org: Create test organization")
    test_org = Organization.api_create(session_context)
    TestData.test_org = test_org
    return test_org


@pytest.fixture(scope="session")
def test_space(request, test_org):
    log_fixture("test_space: Create test space")
    TestData.test_space = Space.api_create(test_org)
    return TestData.test_space


@pytest.fixture(scope="session")
def test_org_manager(request, session_context, test_org):
    log_fixture("test_org_manager: Add org manager to test org")
    test_org_manager = User.api_create_by_adding_to_organization(session_context, org_guid=test_org.guid)
    TestData.test_org_manager = test_org_manager
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


@pytest.fixture(scope="class")
def login_to_cf_core(core_org, core_space):
     log_fixture("login_to_cf_core: Login to cf targeting core org and core space")
     cf.cf_login(core_org.name, core_space.name)


@pytest.fixture(scope="class")
def sample_python_app(request, class_context, test_org, test_space):
    log_fixture("sample_python_app: Push app to cf")
    cf.cf_login(test_org.name, test_space.name)
    app = Application.push(context=class_context, space_guid=test_space.guid,
                           source_directory=ApplicationPath.SAMPLE_PYTHON_APP)
    log_fixture("Check the application is running")
    app.ensure_started()
    return app


@pytest.fixture(scope="class")
def sample_java_app(request, class_context, test_org, test_space):
    test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
    log_fixture("sample_java_app: Compile the sources")
    test_app_sources.compile_mvn()
    log_fixture("sample_java_app: Push app to cf")
    cf.cf_login(test_org.name, test_space.name)
    app = Application.push(context=class_context, space_guid=test_space.guid,
                           source_directory=ApplicationPath.SAMPLE_JAVA_APP)
    log_fixture("Check the application is running")
    app.ensure_started()
    return app


@pytest.fixture(scope="class")
def sample_service(class_context, request, test_org, test_space, sample_python_app):
    log_fixture("sample_service: Register sample app in marketplace")
    service = ServiceType.register_app_in_marketplace(context=class_context,
                                                      app_name=sample_python_app.name,
                                                      app_guid=sample_python_app.guid,
                                                      org_guid=test_org.guid,
                                                      space_guid=test_space.guid)
    log_fixture("sample_service: Get service plans")
    service.api_get_service_plans()
    return service


@pytest.fixture(scope="session")
def admin_user():
    log_fixture("admin_user: Retrieve admin user")
    admin_user = User.cf_api_get_user(config.admin_username)
    admin_user.password = config.admin_password
    TestData.admin_user = admin_user
    return admin_user


@pytest.fixture(scope="session")
def admin_client():
    log_fixture("admin_client: Get http client for admin")
    TestData.admin_client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return TestData.admin_client


@pytest.fixture(scope="session")
def space_users_clients(request, session_context, test_org, test_space, admin_client):
    log_fixture("clients: Create clients")
    clients = {}
    for role, value in User.SPACE_ROLES.items():
        clients[role] = User.api_create_by_adding_to_space(session_context, org_guid=test_org.guid, space_guid=test_space.guid,
                                                           roles=value).login()
    clients["admin"] = admin_client
    return clients


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
    ref_org_name = config.core_org_name
    orgs = Organization.cf_api_get_list()
    TestData.core_org = next(o for o in orgs if o.name == ref_org_name)
    return TestData.core_org


@pytest.fixture(scope="session")
def core_space():
    log_fixture("core_space: Create object for core space")
    ref_space_name = config.core_space_name
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


@pytest.fixture(scope="session")
def psql_instance(session_context, test_org, test_space):
    log_fixture("create_postgres_instance")
    marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
    psql = next(service for service in marketplace if service.label == ServiceLabels.PSQL)
    TestData.psql_instance = ServiceInstance.api_create(
        context=session_context,
        org_guid=test_org.guid,
        space_guid=test_space.guid,
        service_label=ServiceLabels.PSQL,
        service_plan_guid=psql.service_plan_guids[0]
    )
    return TestData.psql_instance


@pytest.fixture(scope="session")
def psql_app(psql_instance, session_context):
    sql_api_sources = AppSources.from_github(repo_name=TapGitHub.sql_api_example,
                                             repo_owner=TapGitHub.intel_data,
                                             gh_auth=config.github_credentials())
    TestData.psql_app = Application.push(
        context=session_context,
        space_guid=TestData.test_space.guid,
        source_directory=sql_api_sources.path,
        bound_services=(psql_instance.name,)
    )
    return TestData.psql_app


@pytest.fixture(scope="session")
def model_hdfs_path(request, session_context, test_org, add_admin_to_test_org):
    log_fixture("Create a transfer and get hdfs path")
    _, data_set = data_catalog.create_dataset_from_link(session_context, org=test_org, source=Urls.model_url)
    return data_set.target_uri


