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

import base64
import io
import json
import os

import pytest

import config
from modules.app_sources import AppSources
from modules.constants import ApplicationPath, HttpStatus, ServiceLabels, ServicePlan, TapApplicationType, \
    TapComponent, TapGitHub
from modules.exceptions import UnexpectedResponseError
from modules.file_utils import zip_file
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.configuration_provider.k8s_service import ServiceConfigurationProvider
from modules.ssh_lib import JumpClient
from modules.tap_logger import log_fixture, log_finalizer
from modules.tap_object_model import Application, Organization, ServiceOffering, ServiceInstance, User,\
    ScoringEngineModel, ModelArtifact
from modules.tap_object_model.prep_app import PrepApp
from modules.tap_object_model.flows import data_catalog
from modules.test_names import generate_test_object_name
from tap_component_config import api_service
from .data_repo import Urls, DATA_REPO_PATH, DataFileKeys
from .sample_apps import SampleApps


# TODO until unittest.TestCase subclassing is not removed, session-scoped fixtures write to global variables
# TODO logger in fixtures should have special format


@pytest.fixture(scope="session")
def api_service_admin_client():
    api_version = api_service[TapComponent.api_service]["api_version"]
    default_url = "{}://{}/api/{}".format(config.external_protocol, config.api_url, api_version)
    return HttpClientFactory.get(ServiceConfigurationProvider.get(url=default_url))


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
    return ScoringEngineModel.create(context, org_guid=core_org.guid, description="Test model", revision="revision",
                                     algorithm="algorithm", creation_tool="creationTool")


@pytest.fixture(scope="function")
def model_with_artifact(request, context, core_org):
    log_fixture("test_model: Create test model and add artifact")
    model = ScoringEngineModel.create(context, org_guid=core_org.guid, description="Test model", revision="revision",
                                      algorithm="algorithm", creation_tool="creationTool")
    ModelArtifact.upload_artifact(model_id=model.id, filename="example_artifact.txt",
                                  actions=[ModelArtifact.ARTIFACT_ACTIONS["publish_jar_scoring_engine"]])
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


def push_app_from_tar(context, app_path):
    archive_path = os.path.join(app_path, 'app.tar.gz')
    log_fixture('using existing archive to push app: {}'.format(archive_path))

    app_name = generate_test_object_name(separator='')

    manifest_path = os.path.join(app_path, 'manifest.json')
    with open(manifest_path) as manifest_file:
        manifest = json.load(manifest_file)
        manifest['name'] = app_name

    return Application.push(context, app_path=archive_path,
                            name=app_name, manifest=manifest,
                            client=api_service_admin_client())


@pytest.fixture(scope="class")
def sample_python_app(class_context):
    log_fixture("sample_python_app: push sample application")
    if not os.path.exists(ApplicationPath.SAMPLE_PYTHON_APP_TAR):
        test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_PYTHON_APP)
        test_app_sources.run_build_sh()

    app = push_app_from_tar(class_context, ApplicationPath.SAMPLE_PYTHON_APP)

    log_fixture("sample_python_app: Check the application is running")
    app.ensure_running()
    log_fixture("sample_python_app: Check the application is responding")
    app.ensure_responding()
    return app


@pytest.fixture(scope="class")
def compiled_sample_java_app():
    log_fixture("compiled_sample_java_app: download libraries")
    test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_JAVA_APP)
    test_app_sources.run_build_sh()
    return test_app_sources.path


@pytest.fixture(scope="class")
def sample_app_jar(compiled_sample_java_app):
    jar_directory = os.path.join(compiled_sample_java_app, "target")
    file_list = os.listdir(jar_directory)
    return os.path.join(jar_directory, next(name for name in file_list if name.endswith(".jar")))


@pytest.fixture(scope="class")
def sample_java_app(class_context):
    log_fixture("sample_java_app: Push app to tap")
    if not os.path.exists(ApplicationPath.SAMPLE_JAVA_APP_TAR):
        compiled_sample_java_app()

    app = push_app_from_tar(class_context, ApplicationPath.SAMPLE_JAVA_APP)

    log_fixture("sample_java_app: Check the application is running")
    app.ensure_running()
    log_fixture("sample_java_app: Check the application is responding")
    app.ensure_responding()
    return app


@pytest.fixture(scope="class")
def compiled_sample_go_app():
    log_fixture("compiled_sample_go_app: download libraries")
    test_app_sources = AppSources.from_local_path(sources_directory=ApplicationPath.SAMPLE_GO_APP)
    test_app_sources.run_build_sh()
    return test_app_sources.path


@pytest.fixture(scope="class")
def sample_go_app(class_context):
    log_fixture("sample_go_app: Compile go app")
    if not os.path.exists(ApplicationPath.SAMPLE_GO_APP_TAR):
        compiled_sample_go_app()

    app = push_app_from_tar(class_context, ApplicationPath.SAMPLE_GO_APP)

    log_fixture("sample_go_app: Check the application is running")
    app.ensure_running()
    log_fixture("sample_go_app: Check the application is responding")
    app.ensure_responding()
    return app


@pytest.fixture(scope="class")
def space_shuttle_application(class_context):
    SPACE_SHUTTLE_DEMO_APP_NAME = "space-shuttle-demo"

    log_fixture(SPACE_SHUTTLE_DEMO_APP_NAME + ": Get all information about application")
    app = Application.get_by_name(SPACE_SHUTTLE_DEMO_APP_NAME)

    return app


@pytest.fixture(scope="session")
def psql_instance(session_context, api_service_admin_client):
    log_fixture("create_postgres_instance")
    psql = ServiceInstance.create_with_name(context=session_context, client=api_service_admin_client,
                                            offering_label=ServiceLabels.PSQL, plan_name=ServicePlan.SINGLE_SMALL)
    log_fixture("Check the service instance is running")
    psql.ensure_running()
    return psql


@pytest.fixture(scope="session")
def mysql_instance(session_context, api_service_admin_client):
    log_fixture("create_mysql_instance")
    mysql = ServiceInstance.create_with_name(context=session_context, client=api_service_admin_client,
                                             offering_label=ServiceLabels.MYSQL, plan_name=ServicePlan.SINGLE_SMALL)
    log_fixture("Check the service instance is running")
    mysql.ensure_running()
    return mysql


@pytest.fixture(scope="session")
def orientdb_instance(session_context, api_service_admin_client):
    log_fixture("orientdb_instance: create")
    orientdb = ServiceInstance.create_with_name(context=session_context,
                                                client=api_service_admin_client,
                                                offering_label=ServiceLabels.ORIENT_DB,
                                                plan_name=ServicePlan.SINGLE_SMALL)
    log_fixture("orientdb_instance: ensure instance is running")
    orientdb.ensure_running()
    return orientdb


@pytest.fixture(scope="session")
def mongodb_instance(session_context, api_service_admin_client):
    log_fixture("create_mongodb_instance")
    mysql = ServiceInstance.create_with_name(context=session_context, client=api_service_admin_client,
                                             offering_label=ServiceLabels.MONGO_DB_30,
                                             plan_name=ServicePlan.SINGLE_SMALL)
    log_fixture("Check the service instance is running")
    mysql.ensure_running()
    return mysql


@pytest.fixture(scope="class")
def kafka_instance(session_context, api_service_admin_client):
    log_fixture("create_kafka_instance")
    kafka = ServiceInstance.create_with_name(context=session_context, offering_label=ServiceLabels.KAFKA,
                                     plan_name=ServicePlan.SHARED, client=api_service_admin_client)
    log_fixture("Check the service instance is running")
    kafka.ensure_running()
    return kafka


@pytest.fixture(scope="class")
def hdfs_instance(session_context, api_service_admin_client):
    log_fixture("create_hdfs_instance")
    hdfs = ServiceInstance.create_with_name(context=session_context, offering_label=ServiceLabels.HDFS,
                                            plan_name=ServicePlan.ENCRYPTED_DIR, client=api_service_admin_client)
    log_fixture("Check the service instance is running")
    hdfs.ensure_running()
    return hdfs


@pytest.fixture(scope="class")
def kerberos_instance(session_context, api_service_admin_client):
    log_fixture("create_kerberos_instance")
    kerberos = ServiceInstance.create_with_name(context=session_context, offering_label=ServiceLabels.KERBEROS,
                                     plan_name=ServicePlan.SHARED, client=api_service_admin_client)
    log_fixture("Check the service instance is running")
    kerberos.ensure_running()
    return kerberos


@pytest.fixture(scope="module")
def app_bound_mongodb(module_context, mongodb_instance, api_service_admin_client):
    log_fixture("mongodb_app: download libraries")
    app_src = AppSources.from_local_path(ApplicationPath.MONGODB_API)
    p_a = PrepApp(app_src.path)
    log_fixture("mongodb_app: package sample application")
    if os.path.exists(ApplicationPath.MONGODB_API_TAR):
        gzipped_app_path = ApplicationPath.MONGODB_API_TAR
    else:
        gzipped_app_path = p_a.package_app(module_context)

    log_fixture("mongodb_app: update manifest")
    manifest_params = {"type": TapApplicationType.PYTHON27, "bindings": [mongodb_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("mongodb_app: push sample application")
    db_app = Application.push(module_context, app_path=gzipped_app_path,
                              name=p_a.app_name, manifest_path=manifest_path,
                              client=api_service_admin_client)

    log_fixture("mongodb_app: Check the application is running")
    db_app.ensure_running()

    log_fixture("mongodb_app: Check the application is responding")
    db_app.ensure_responding()
    return db_app


@pytest.fixture(scope="module")
def app_bound_mysql(module_context, mysql_instance, api_service_admin_client):
    log_fixture("mysql_app: download libraries")
    app_src = AppSources.from_local_path(ApplicationPath.SQL_API_EXAMPLE)
    p_a = PrepApp(app_src.path)
    log_fixture("mysql_app: package sample application")
    if os.path.exists(ApplicationPath.SQL_API_EXAMPLE_TAR):
        gzipped_app_path = ApplicationPath.SQL_API_EXAMPLE_TAR
    else:
        gzipped_app_path = p_a.package_app(module_context)

    log_fixture("mysql_app: update manifest")
    manifest_params = {"type": TapApplicationType.PYTHON27, "bindings": [mysql_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("mysql_app: push sample application")
    db_app = Application.push(module_context, app_path=gzipped_app_path,
                              name=p_a.app_name, manifest_path=manifest_path,
                              client=api_service_admin_client)

    log_fixture("mysql_app: Check the application is running")
    db_app.ensure_running()

    log_fixture("mysql_app: Check the application is responding")
    db_app.ensure_responding()
    return db_app


@pytest.fixture(scope="module")
def app_bound_orientdb(module_context, orientdb_instance, api_service_admin_client):
    log_fixture("orientdb_app: download libraries")
    app_src = AppSources.from_local_path(ApplicationPath.ORIENTDB_API)
    app_src.run_build_sh()

    log_fixture("orientdb_app: package sample application")
    p_a = PrepApp(app_src.path)
    gzipped_app_path = p_a.package_app(module_context)

    log_fixture("orientdb_app: update manifest")
    manifest_params = {"type": TapApplicationType.PYTHON27, "bindings": [orientdb_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("orientdb_app: push orientdb-api application")
    application = Application.push(module_context,
                                   app_path=gzipped_app_path,
                                   name=p_a.app_name,
                                   manifest_path=manifest_path,
                                   client=api_service_admin_client)
    log_fixture("orientdb_app: Ensure app is running")
    application.ensure_running()
    log_fixture("orientdb_app: Ensure app is responding")
    application.ensure_responding()
    return application


@pytest.fixture(scope="module")
def app_bound_psql(module_context, psql_instance, api_service_admin_client):
    log_fixture("psql_app: Download libraries")
    app_src = AppSources.from_local_path(ApplicationPath.SQL_API_EXAMPLE)
    p_a = PrepApp(app_src.path)
    log_fixture("psql_app: package sample application")
    if os.path.exists(ApplicationPath.SQL_API_EXAMPLE_TAR):
        gzipped_app_path = ApplicationPath.SQL_API_EXAMPLE_TAR
    else:
        gzipped_app_path = p_a.package_app(module_context)

    log_fixture("psql_app: update manifest")
    manifest_params = {"type": TapApplicationType.PYTHON27, "bindings": [psql_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("psql_app: push sample application")
    db_app = Application.push(module_context, app_path=gzipped_app_path,
                              name=p_a.app_name, manifest_path=manifest_path,
                              client=api_service_admin_client)

    log_fixture("psql_app: Check the application is running")
    db_app.ensure_running()

    log_fixture("psq_app: Check the application is responding")
    db_app.ensure_responding()
    return db_app


@pytest.fixture(scope="class")
def ws2kafka_app(class_context, kafka_instance, api_service_admin_client):
    log_fixture("ws2kafka: download libraries")
    ingestion_repo = AppSources.get_repository(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=TapGitHub.intel_data)
    ws2kafka_path = os.path.join(ingestion_repo.path, TapGitHub.ws2kafka)
    build_path = os.path.join(ws2kafka_path, "deploy")
    ingestion_repo.run_build_sh(cwd=build_path, command="./pack.sh")
    app_path = os.path.join(build_path, "ws2kafka.tar.gz")

    log_fixture("ws2kafka: update manifest")
    p_a = PrepApp(build_path)
    manifest_params = {"bindings": [kafka_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("ws2kafka: push application")
    app = Application.push(class_context, app_path=app_path,
                           name=p_a.app_name, manifest_path=manifest_path,
                           client=api_service_admin_client)

    log_fixture("ws2kafka: Check the application is running")
    app.ensure_running()
    return app


@pytest.fixture(scope="class")
def kafka2hdfs_app(class_context, kafka_instance, hdfs_instance, kerberos_instance, api_service_admin_client):
    log_fixture("kafka2hdfs: download libraries")
    ingestion_repo = AppSources.get_repository(repo_name=TapGitHub.ws_kafka_hdfs, repo_owner=TapGitHub.intel_data)
    kafka2hdfs_path = os.path.join(ingestion_repo.path, TapGitHub.kafka2hdfs)

    log_fixture("Package kafka2hdfs app")
    ingestion_repo.compile_gradle(working_directory=kafka2hdfs_path)

    build_path = os.path.join(kafka2hdfs_path, "deploy")
    ingestion_repo.run_build_sh(cwd=build_path, command="./pack.sh")
    app_path = os.path.join(build_path, "kafka2hdfs.tar")

    log_fixture("kafka2hdfs: update manifest")
    p_a = PrepApp(build_path)
    manifest_params = {"bindings": [kafka_instance.name, hdfs_instance.name, kerberos_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("kafka2hdfs: push application")
    app = Application.push(class_context, app_path=app_path,
                           name=p_a.app_name, manifest_path=manifest_path,
                           client=api_service_admin_client)

    log_fixture("kafka2hdfs: Check the application is running")
    app.ensure_running()
    return app


@pytest.fixture(scope="class")
def hbase_reader_app(class_context, kerberos_instance, api_service_admin_client):
    log_fixture("hbase_reader: download libraries")
    hbase_reader_repo = AppSources.get_repository(repo_name=TapGitHub.hbase_api_example, repo_owner=TapGitHub.intel_data)

    log_fixture("Package hbase_reader app")

    build_path = os.path.join(hbase_reader_repo.path, "deploy")
    hbase_reader_repo.run_build_sh(cwd=build_path, command="./pack.sh")
    app_path = os.path.join(build_path, "hbase-java-api-example-0.1.1.tar")

    log_fixture("hbase_reader: update manifest")
    p_a = PrepApp(build_path)
    manifest_params = {"bindings": [kerberos_instance.name]}
    manifest_path = p_a.update_manifest(params=manifest_params)

    log_fixture("hbase_reader: push application")
    app = Application.push(class_context, app_path=app_path,
                           name=p_a.app_name, manifest_path=manifest_path,
                           client=api_service_admin_client)

    log_fixture("hbase_reader: Check the application is running")
    app.ensure_running()
    return app


@pytest.fixture(scope="class")
def sample_service_from_template(class_context):
    log_fixture("Create new example service")
    sample_service = ServiceOffering.create(context=class_context)
    log_fixture("Check the service is ready")
    sample_service.ensure_ready()
    return sample_service


@pytest.fixture(scope="class")
def sample_service(class_context, sample_app_jar):
    log_fixture("Prepare mainfest and offering json")
    offering_json = ServiceOffering.create_offering_json()
    manifest_json = ServiceOffering.create_manifest_json(app_type=TapApplicationType.JAVA)
    log_fixture("Create new example service from binary")
    sample_service = ServiceOffering.create_from_binary(class_context, jar_path=sample_app_jar,
                                                        manifest_path=manifest_json, offering_path=offering_json)
    log_fixture("Check the service is ready")
    sample_service.ensure_ready()
    return sample_service


@pytest.fixture(scope="session")
def admin_user(test_org):
    log_fixture("admin_user: Retrieve admin user")
    admin_user = User.get_admin(test_org.guid)
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
    admin_user.add_to_organization(org_guid=test_org.guid)


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
def model_hdfs_path(session_context, core_org, test_data_urls):
    model_file = zip_file(test_data_urls[DataFileKeys.SCORING_ENGINE_MODEL].filepath)  # workaround for DPNG-15187
    log_fixture("Create a dataset with model file.")
    _, dataset = data_catalog.create_dataset_from_file(session_context, core_org.guid, model_file)
    return dataset.target_uri


@pytest.fixture(scope="session")
def test_data_urls(session_context):
    """ Fixture with files from tests/fixtures/data_repo.py::DATA_FILES.
        They are accessible by url or filepath.
        Eg.:
            test_data_urls.test_transfer.url
            test_data_urls['test_transfer'].url
            test_data_urls.test_transfer.filepath
    """
    if config.data_repo_url:
        return Urls(config.data_repo_url)
    else:
        log_fixture("data_repo: package sample application")
        p_a = PrepApp(DATA_REPO_PATH)
        gzipped_app_path = p_a.package_app(session_context)

        log_fixture("data_repo: update manifest")
        manifest_path = p_a.update_manifest(params={})

        log_fixture("data_repo: Push data_repo application")
        app = Application.push(context=session_context, app_path=gzipped_app_path, name=p_a.app_name,
                               manifest_path=manifest_path)

        log_fixture("data_repo: Check application is running")
        app.ensure_running()

        return Urls(app.urls[0])


@pytest.yield_fixture(scope="session")
def test_sample_apps():
    log_fixture("test_sample_apps: Copy sample_apps to temporary directory, build and pack them")
    sample_apps = SampleApps()
    yield sample_apps
    log_fixture("test_sample_apps: delete sample_apps temporary directory")
    sample_apps.cleanup()
