#!/usr/bin/env python
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

import io
import os

from modules.constants import Priority, TapComponent
from modules.runner.loader import TapTestLoader
from modules.tap_logger import get_logger


logger = get_logger(__name__)


TEST_PATHS = [
    directory for directory in os.listdir(TapTestLoader.ROOT_DIRECTORY)
    if directory.startswith("test_") and os.path.isdir(os.path.join(TapTestLoader.ROOT_DIRECTORY, directory))
]


def count_by_priority(loader: TapTestLoader):
    priority_stats = {key: 0 for key in Priority.names()}
    for test in loader.tests:
        priority = getattr(test, "priority", None)
        if priority is not None:
            priority_stats[priority.name] += 1
    return priority_stats


def count_by_component(loader: TapTestLoader):
    component_stats = {key: 0 for key in TapComponent.names()}
    for test in loader.tests:
        components = getattr(test, "components", None)
        if components is not None:
            for component in components:
                component_stats[component.name] += 1
    return component_stats


def log_stats(stats: dict, stat_name: str):
    output = io.StringIO()
    output.write("\n{}\n".format(stat_name))
    for name, count in stats.items():
        if count > 0:
            output.write("\t{}: {}\n".format(name, count))
    logger.info(output.getvalue())


def log_all_stats(directory=None, show_priorities=False, show_components=False):
    directory_names = TEST_PATHS if directory is None else [directory]
    for directory_name in directory_names:
        loader = TapTestLoader()
        loader.load(path=directory_name)
        logger.info("Tests in {}: {}".format(directory_name, len(loader.tests)))
        if show_priorities:
            log_stats(count_by_priority(loader), "Priority")
        if show_components:
            log_stats(count_by_component(loader), "Components")
