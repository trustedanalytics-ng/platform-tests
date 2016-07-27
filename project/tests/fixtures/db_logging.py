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
from modules.constants import TapComponent
from modules.mongo_reporter.reporter import MongoReporter


def get_tap_components_from_request(request):
    tap_component_names = TapComponent.names()
    components = set()
    for i in range(0, len(request.session.items)):
        keywords = request.session.items[i].keywords.items()
        for keyword in keywords:
            if keyword[0] in tap_component_names:
                components.add(keyword[0])
    return sorted(list(components))


@pytest.fixture(scope="session", autouse=True)
def log_test_run_in_database(request):
    if config.database_url is not None:
        mongo_reporter = MongoReporter(mongo_uri=config.database_url, run_id=config.test_run_id)
        mongo_reporter.on_run_start(environment=config.tap_domain,
                                    environment_version=config.tap_version,
                                    infrastructure_type=config.tap_infrastructure_type,
                                    appstack_version=config.appstack_version,
                                    platform_components=[],
                                    components=get_tap_components_from_request(request),
                                    tests_to_run_count=len(request.session.items))

        def finalizer():
            mongo_reporter.on_run_end()
        request.addfinalizer(finalizer)
