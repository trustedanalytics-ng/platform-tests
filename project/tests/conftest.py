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
import re
from collections import Counter, namedtuple
from itertools import groupby

import pytest
import requests
from _pytest.mark import MarkInfo, MarkDecorator

import config
from modules.constants import Path, ParametrizedService
from modules.mongo_reporter.reporter import MongoReporter
from modules.mongo_reporter.request_reporter import request_reporter
from modules.tap_logger import get_logger
from modules.tap_object_model import ServiceOffering

pytest_plugins = ["tests.fixtures.context",
                  "tests.fixtures.fixtures",
                  "tests.fixtures.fixtures_core_components",
                  "tests.fixtures.remote_logging",
                  "tests.fixtures.fixtures_ng",
                  "modules.mongo_reporter.request_reporter"]


logger = get_logger(__name__)


INCREMENTAL_KEYWORD = "incremental"

mongo_reporter = MongoReporter(run_id=config.test_run_id)


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


def pytest_addoption(parser):
    parser.addoption("--only-with-param", type=str, action="store", metavar="PARAMETER",
                     help="run only tests with parameter (for performance test)")


def pytest_collection_modifyitems(config, items):
    """
    Support for running tests with component tags.
    Report all test component markers to mongo_reporter.
    """
    only_param = config.getoption("only_with_param")
    if only_param is not None:
        items[:] = [i for i in items if only_param in i.name]

    if config.option.collectonly:
        _log_skip_statistic(items)

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


def _log_skip_statistic(items):
    issue_stats, other_tests = _calc_statistics(items)
    _log_labeled_stats(issue_stats)
    _log_others(other_tests)


def _calc_statistics(items):
    skipped_items = _get_skipped_items(items)
    issue_numbers = []
    other_tests = []
    for item in skipped_items:
        match = re.search("DPNG-\d+", item.reason)
        if match:
            issue_numbers.append(match.group(0))
        else:
            issue_numbers.append('others')
            other_tests.append(item)
    return Counter(issue_numbers), other_tests


SkippedItem = namedtuple("SkippedItem", "test_name reason")


def _get_skipped_items(items):
    skipped_items = [item for item in items if item.keywords.get('skip') is not None]
    items = []
    for item in skipped_items:
        skip_info = item.keywords.get('skip')
        if isinstance(skip_info, (MarkInfo, MarkDecorator)):
            if 'reason' in skip_info.kwargs:
                reason = skip_info.kwargs['reason']
            elif skip_info.args:
                reason = skip_info.args[0]
            else:
                reason = ''
            items.append(SkippedItem(item.nodeid, reason))
    return items


def _log_labeled_stats(issues):
    msg = ["Skipped tests statistic:"]
    issues_sorted_by_quantity = sorted(issues.items(), key=lambda i: i[1], reverse=True)
    for issue, quantity in issues_sorted_by_quantity:
        msg.append("{:>11}: {:>6}".format(issue, quantity))
    logger.info("\n".join(msg))


def _log_others(other_items):
    msg = ["Skipped tests not labeled with issue:"]
    items_grouped_by_reason = groupby(other_items, key=lambda i: i.reason)
    for reason, items in items_grouped_by_reason:
        msg.append("{}:".format(reason))
        msg.extend("|---{}".format(item.test_name) for item in items)
    logger.info("\n".join(msg))
    pass


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
    inserted_id = mongo_reporter.log_report(report, item)

    if inserted_id:
        test_name = item.nodeid.split('::')[-1]
        request_reporter.send_to_db(test_name=test_name, result_document_id=inserted_id)

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


def pytest_runtest_call(item):
    """ Log test start """
    test_name = item.location[2]
    separator = "*" * len(test_name)
    logger.info("\n{0}\n\n{1}\n\n{0}\n".format(separator, test_name))


def pytest_generate_tests(metafunc):
    """Parametrize marketplace fixture with tuples of ServiceOffering and plan dict."""
    if "non_parametrized_marketplace_services" in metafunc.funcargnames:
        marketplace = ServiceOffering.get_list()
        test_cases = []
        ids = []
        for offering in marketplace:
            if offering.service_plans is not None:
                for plan in offering.service_plans:
                    if not ParametrizedService.is_parametrized(label=offering.label, plan_name=plan.name):
                        test_cases.append((offering, plan))
                        ids.append("{}_{}".format(offering.label, plan.name))
        metafunc.parametrize("non_parametrized_marketplace_services", test_cases, ids=ids)


def pytest_sessionfinish(session, exitstatus):
    mongo_reporter.on_run_end()
