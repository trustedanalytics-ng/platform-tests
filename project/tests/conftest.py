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
from modules.constants import Path, ServiceLabels, ParametrizedService
from modules.mongo_reporter.reporter import MongoReporter
from modules.tap_logger import get_logger
from modules.tap_object_model import ServiceType
import tests.fixtures.fixtures as fixtures


pytest_plugins = ["tests.fixtures.context", "tests.fixtures.db_logging", "tests.fixtures.fixtures",
                  "tests.fixtures.remote_logging"]


logger = get_logger(__name__)


INCREMENTAL_KEYWORD = "incremental"


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

    if config.CONFIG["database_url"] is not None:
        mongo_reporter = MongoReporter(mongo_uri=config.CONFIG["database_url"], run_id=config.CONFIG["test_run_id"])
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


def pytest_generate_tests(metafunc):
    """Parametrize marketplace fixture with tuples of ServiceType and plan dict."""
    if "non_parametrized_marketplace_services" in metafunc.funcargnames:
        core_space = fixtures.core_space()
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=core_space.guid)
        test_cases = []
        ids = []
        for service_type in marketplace:
            for plan in service_type.service_plans:
                if not ParametrizedService.is_parametrized(label=service_type.label, plan_name=plan["name"]):
                    test_cases.append((service_type, plan))
                    ids.append("{}_{}".format(service_type.label, plan["name"]))
        metafunc.parametrize("non_parametrized_marketplace_services", test_cases, ids=ids)

