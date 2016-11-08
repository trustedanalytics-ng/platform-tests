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
import io
import os

import pytest

import config
from modules.app_sources import AppSources
from modules.constants import ApplicationPath, HttpStatus, TapApplicationType, ServiceLabels, ServicePlan
from modules.exceptions import UnexpectedResponseError, ModelNotFoundException
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.configuration_provider.k8s_service import ServiceConfigurationProvider
from modules.tap_logger import log_fixture, log_finalizer
from modules.tap_object_model import Application, Organization, ServiceOffering, ServiceInstance, User,\
    ScoringEngineModel, ModelArtifact, Binding
from modules.tap_object_model.flows import data_catalog


# TODO until unittest.TestCase subclassing is not removed, session-scoped fixtures write to global variables
# TODO logger in fixtures should have special format


@pytest.fixture(scope="session")
def api_service_admin_client():
    return HttpClientFactory.get(ServiceConfigurationProvider.get())


@pytest.fixture(scope="session")
def test_org(request, core_org):
    # Workaround due to limited org management in TAP v0.8
    log_fixture("test_org: Returns core org")
    return core_org


@pytest.fixture(scope="session")
def test_org_user(request, session_context, test_org):
    log_fixture("test_org_user: Add user to test org")
    return User.create_by_adding_to_organization(context=session_context, org_guid=test_org.guid,
                                                 role=User.ORG_ROLE["user"])


@pytest.fixture(scope="session")
def test_space(request, test_org):
    raise NotImplementedError("Test needs refactoring. Spaces are no longer supported on TAP")


@pytest.fixture(scope="session")
def test_org_user_client(test_org_user):
    log_fixture("test_org_user_client: Login as test org user")
    test_org_user_client = test_org_user.login()
    return test_org_user_client


@pytest.fixture(scope="session")
def test_org_admin(request, session_context, test_org):
    log_fixture("test_org_user: Add admin to test org")
    return User.create_by_adding_to_organization(context=session_context, org_guid=test_org.guid,
                                                 role=User.ORG_ROLE["admin"])


@pytest.fixture(scope="session")
def test_org_admin_client(test_org_admin):
    log_fixture("test_org_admin_client: Login as test org admin")
    return test_org_admin.login()


@pytest.fixture(scope="class")
def test_user_clients(test_org_admin_client, test_org_user_client):
    return {
        "user": test_org_user_client,
        "admin": test_org_admin_client
    }


@pytest.fixture(scope="function")
def sample_model(request, context, core_org):
    log_fixture("test_model: Create test model")
    return ScoringEngineModel.create(context, org_guid=core_org.guid, name="test-model", description="Test model",
                                     revision="revision", algorithm="algorithm", creation_tool="creationTool")


@pytest.fixture(scope="function")
def model_with_artifact(request, context, core_org):
    log_fixture("test_model: Create test model and add artifact")
    model = ScoringEngineModel.create(context, org_guid=core_org.guid, name="test-model", description="Test model",
                                      revision="revision", algorithm="algorithm", creation_tool="creationTool")
    ModelArtifact.upload_artifact(model_id=model.id, filename="example_artifact.txt",
                                  actions=[ModelArtifact.ARTIFACT_ACTIONS["publish_to_marketplace"]])
    return ScoringEngineModel.get(model_id=model.id)


@pytest.fixture(scope="class")
def login_to_cf(test_org, test_space):
    raise NotImplementedError("Test needs refactoring. CF is no longer a part of TAP")


@pytest.fixture(scope="class")
def login_to_cf_core(core_org, core_space):
    raise NotImplementedError("Test needs refactoring. CF is no longer a part of TAP")


@pytest.fixture(scope="class")
def marketplace_offerings():
    log_fixture("Get list of available services from Marketplace")
    return ServiceOffering.get_list()


@pytest.fixture(scope="class")
def sample_python_app(class_context, tap_cli):
    log_fixture("sample_python_app: push sample application")
    cwd = ApplicationPath.SAMPLE_PYTHON_APP
    app = Application.push(class_context, app_path=cwd, tap_cli=tap_cli,
                           app_type=TapApplicationType.PYTHON27)
    log_fixture("Check the application is running")
    app.ensure_running()
    return app


@pytest.fixture(scope="class")
def sample_java_app(class_context, tap_cli):
    test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
    log_fixture("sample_java_app: Compile the sources")
    test_app_sources.compile_mvn()
    log_fixture("sample_java_app: Push app to tap")
    app = Application.push(context=class_context, app_path=ApplicationPath.SAMPLE_JAVA_APP, tap_cli=tap_cli,
                           app_type=TapApplicationType.JAVA)
    app.ensure_running()
    return app


@pytest.fixture(scope="session")
def psql_instance(session_context, api_service_admin_client):
    log_fixture("create_postgres_instance")
    psql = ServiceInstance.create_with_name(context=session_context, client=api_service_admin_client,
                                            offering_label=ServiceLabels.PSQL, plan_name=ServicePlan.FREE)
    log_fixture("Check the service instance is running")
    psql.ensure_running()
    return psql


@pytest.fixture(scope="session")
def mysql_instance(session_context, api_service_admin_client):
    log_fixture("create_mysql_instance")
    mysql = ServiceInstance.create_with_name(context=session_context, client=api_service_admin_client,
                                             offering_label=ServiceLabels.MYSQL, plan_name=ServicePlan.FREE)
    log_fixture("Check the service instance is running")
    mysql.ensure_running()
    return mysql


@pytest.fixture(scope="class")
def app_binded_mysql(class_context, tap_cli, mysql_instance, api_service_admin_client):
    log_fixture("mysql_app: push sample application")
    app_src = AppSources.from_local_path(ApplicationPath.SQL_API_EXAMPLE)
    app_src.run_build_sh()
    db_app = Application.push(class_context, app_path=app_src.path, tap_cli=tap_cli,
                              app_type=TapApplicationType.PYTHON27)
    log_fixture("Check the application is running")
    db_app.ensure_running()
    Binding.create(client=api_service_admin_client, context=class_context,
                   app_id=db_app.id, service_instance_id=mysql_instance.id)
    log_fixture("Check the application is responding")
    db_app.ensure_responding()
    return db_app


@pytest.fixture(scope="class")
def app_binded_psql(class_context, tap_cli, psql_instance, api_service_admin_client):
    log_fixture("psql_app: push sample application")
    app_src = AppSources.from_local_path(ApplicationPath.SQL_API_EXAMPLE)
    app_src.run_build_sh()
    db_app = Application.push(class_context, app_path=app_src.path, tap_cli=tap_cli,
                              app_type=TapApplicationType.PYTHON27)
    log_fixture("Check the application is running")
    db_app.ensure_running()
    Binding.create(client=api_service_admin_client, context=class_context,
                   app_id=db_app.id, service_instance_id=psql_instance.id)
    log_fixture("Check the application is responding")
    db_app.ensure_responding()
    return db_app


@pytest.fixture(scope="class")
def sample_service_from_template(class_context):
    log_fixture("Create new example service")
    sample_service = ServiceOffering.create(context=class_context)
    log_fixture("Check the service is ready")
    sample_service.ensure_ready()
    return sample_service


@pytest.fixture(scope="class")
def sample_service(class_context, test_org):
    log_fixture("Create new example service from binary")
    sample_service = ServiceOffering.create_from_binary(class_context, org_guid=test_org.guid)
    log_fixture("Check the service is ready")
    sample_service.ensure_ready()
    return sample_service


@pytest.fixture(scope="session")
def admin_user():
    log_fixture("admin_user: Retrieve admin user")
    admin_user = User.get_admin()
    admin_user.password = config.admin_password
    return admin_user


@pytest.fixture(scope="session")
def admin_client():
    log_fixture("admin_client: Get http client for admin")
    return HttpClientFactory.get(ConsoleConfigurationProvider.get())


@pytest.fixture(scope="session")
def space_users_clients(request, session_context, test_org, test_space, admin_client):
    raise NotImplementedError("Test needs refactoring. Spaces are no longer supported on TAP")


@pytest.fixture(scope="session")
def space_users_clients_core(request, session_context, core_org, core_space, admin_client):
    raise NotImplementedError("Test needs refactoring. Spaces are no longer supported on TAP")


@pytest.fixture(scope="session")
def add_admin_to_test_org(test_org, admin_user):
    log_fixture("add_admin_to_test_org")
    admin_user.api_add_to_organization(org_guid=test_org.guid)


@pytest.fixture(scope="session")
def add_admin_to_test_space(test_org, test_space, admin_user):
    raise NotImplementedError("Test needs refactoring. Spaces are no longer supported on TAP")


@pytest.fixture(scope="session")
def core_org():
    log_fixture("core_org: Create object for core org")
    ref_org_name = config.core_org_name
    orgs = Organization.get_list()
    core_org = next((o for o in orgs if o.name == ref_org_name), None)
    assert core_org is not None, "Could not find org {}".format(ref_org_name)
    return core_org


@pytest.fixture(scope="session")
def core_space():
    raise NotImplementedError("Test needs refactoring. Spaces are no longer supported on TAP")


@pytest.fixture(scope="function")
def remove_admin_from_test_org(admin_user, test_org):
    # TODO: uncomment when multiple organizations are supported
    # log_fixture("Make sure platform admin is not in the organization")
    # try:
    #     admin_user.delete_from_organization(org_guid=test_org.guid)
    # except UnexpectedResponseError as e:
    #     if e.status_code != HttpStatus.CODE_NOT_FOUND:
    #         raise
    return


@pytest.fixture(scope="session")
def test_marketplace():
    log_finalizer("test_marketplace: Get list of marketplace services.")
    return ServiceOffering.get_list()


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
def model_hdfs_path(core_org):
    log_fixture("Retrieve existing model hdfs path from platform")
    model_dataset_name = "model"
    dataset_list = data_catalog.DataSet.api_get_list(org_guid_list=[core_org.guid])
    model_dataset = next((ds for ds in dataset_list if ds.title == model_dataset_name), None)
    if model_dataset is None:
        raise ModelNotFoundException("Model not found. Missing '{}' dataset on platform".format(model_dataset_name))
    return model_dataset.target_uri


@pytest.fixture(scope="session")
def api_service_admin_client():
    return HttpClientFactory.get(ServiceConfigurationProvider.get(url=config.api_url_full_v2))

