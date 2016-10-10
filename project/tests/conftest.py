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

import config
from modules.constants import Path, ParametrizedService
from modules.mongo_reporter import mongo_reporter
from modules.tap_logger import get_logger
from modules.tap_object_model import ServiceType

pytest_plugins = ["tests.fixtures.context",
                  "tests.fixtures.fixtures",
                  "tests.fixtures.fixtures_core_components",
                  "tests.fixtures.remote_logging",
                  "tests.fixtures.fixtures_ng"]


logger = get_logger(__name__)


INCREMENTAL_KEYWORD = "incremental"


def _log_test_configuration():
    logger.info("============== configuration variables ==============")
    pt_env_vars = []
    for key, value in os.environ.items():
        if key.startswith("PT_"):
            if "password" in key.lower():
                value = "*******"
            pt_env_vars.append("{}={}".format(key, value))
    pt_env_vars.sort()
    for env_var in pt_env_vars:
        logger.info(env_var)


def pytest_sessionstart(session):
    """
    Log platform_test environment variables.
    Report test type to mongo_reporter.
    Check environment viability. If the check fails, report unavailable environment and don't start test session.
    """

    _log_test_configuration()

    mongo_reporter.report_test_type(session.config.option.file_or_dir)
    mongo_reporter.report_tap_build_number()

    if not config.ng_disable_environment_check:
        try:
            requests.get(config.console_url, verify=config.ssl_validation).raise_for_status()
            cf_api_url = "{}/info".format(config.cf_api_url_full)
            requests.get(cf_api_url, verify=config.ssl_validation).raise_for_status()
        except Exception as e:
            logger.error("Environment {} is unavailable - {}: {}".format(config.console_url, type(e).__name__, e))
            mongo_reporter.report_unavailable_environment()
            raise


def pytest_collection_modifyitems(items):
    """
    Support for running tests with component tags.
    Report all test component markers to mongo_reporter.
    """
    all_component_markers = []

    for item in items:
        components = item.get_marker("components")
        if components is not None:
            all_component_markers.extend(components)
            for component in components.args:
                item.add_marker(component.replace("-", "_"))

    all_components = []
    for marker in all_component_markers:
        all_components.extend(list(marker.args))
    mongo_reporter.report_components(all_components)


def pytest_collection_finish(session):
    """Logs test statistics for all implemented tests, split by main directory."""
    if session.config.known_args_namespace.collectonly:
        stats = {}
        for item in session.items:
            for directory_name in Path.test_directories:
                if item.location[0].startswith(directory_name):
                    stats[directory_name] = stats.get(directory_name, 0) + 1
        logger.info("==================== test statistics ====================")
        for directory, test_number in stats.items():
            logger.info("{}: {}".format(directory, test_number))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # report for setup, call, teardown
    outcome = yield
    report = outcome.get_result()
    mongo_reporter.log_report(report, item)

    # support for incremental tests
    if INCREMENTAL_KEYWORD in item.keywords:
        if call.excinfo is not None and call.excinfo.typename != "Skipped":
            parent = item.parent
            parent._previous_fail = item


def pytest_runtest_setup(item):
    if INCREMENTAL_KEYWORD in item.keywords:
        previous_fail = getattr(item.parent, "_previous_fail", None)
        if previous_fail is not None:
            pytest.skip("previous test failed ({})".format(previous_fail.name))


def pytest_runtest_logstart(nodeid, location):
    """ signal the start of running a single test item. """
    # TODO implement logging start of a test


def _generate_test_cases(services):
    test_cases = []
    ids = []
    for service_type in services:
        if service_type.service_plans is not None:
            for plan in service_type.service_plans:
                if not ParametrizedService.is_parametrized(label=service_type.label, plan_name=plan["name"]):
                    test_cases.append((service_type, plan))
                    ids.append("{}_{}".format(service_type.label, plan["name"]))
    return test_cases, ids


def pytest_generate_tests(metafunc):
    """Parametrize marketplace fixture with tuples of ServiceType and plan dict."""
    if "non_parametrized_marketplace_services" in metafunc.funcargnames:
        marketplace = ServiceType.api_get_catalog()
        test_cases, ids = _generate_test_cases(marketplace)
        metafunc.parametrize("non_parametrized_marketplace_services", test_cases, ids=ids)


def pytest_sessionfinish(session, exitstatus):
    mongo_reporter.on_run_end()
