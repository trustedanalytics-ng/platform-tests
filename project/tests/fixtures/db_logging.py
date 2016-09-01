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

import config
from modules.mongo_reporter.reporter import MongoReporter, TestRunType


@pytest.fixture(scope="session")
def test_type(request):
    for path in request.config.option.file_or_dir:
        if "test_smoke" in path:
            return TestRunType.API_SMOKE
        if "test_functional" in path:
            return TestRunType.API_FUNCTIONAL


def get_tap_components_from_request(request):
    components = set()
    for i in range(0, len(request.session.items)):
        for component in MongoReporter._marker_args_from_item(item=request.session.items[i], marker_name="components"):
            components.add(component)
    return tuple(sorted(components))


@pytest.fixture(scope="session", autouse=True)
def log_test_run_in_database(request, test_type):
    if config.database_url is not None:
        mongo_reporter = MongoReporter(mongo_uri=config.database_url, run_id=config.test_run_id,
                                       test_run_type=test_type)
        mongo_reporter.on_run_start(environment=config.tap_domain,
                                    environment_version=config.tap_version,
                                    infrastructure_type=config.tap_infrastructure_type,
                                    appstack_version=config.appstack_version,
                                    platform_components=[],
                                    components=[] if request is None else get_tap_components_from_request(request),
                                    environment_availability=False if request is None else True,
                                    kerberos=config.kerberos)

        def finalizer():
            mongo_reporter.on_run_end()

        if request is None:
            finalizer()
        else:
            request.addfinalizer(finalizer)
