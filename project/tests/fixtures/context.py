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

from modules.exceptions import UnexpectedResponseError, CommandExecutionException
from modules.tap_logger import get_logger
from modules.tap_object_model import DataSet


class Context(object):
    logger = get_logger("context")

    def __init__(self):
        self.orgs = []
        self.users = []
        self.invitations = []
        self.transfers = []
        self.apps = []
        self.service_instances = []
        self.bindings = []
        self.service_offerings = []
        self.templates = []
        self.catalog = []
        self.blob_store = []
        self.image_factory = []
        self.k8s_apps = []
        self.models = []
        self.cli_applications = []
        self.cli_services = []
        self.cli_offerings = []

    def _cleanup_test_objects(self, object_list: list):
        while len(object_list) > 0:
            item = object_list.pop()
            try:
                self.logger.info("cleaning: {}".format(item))
                item.cleanup()
            except (UnexpectedResponseError, AssertionError, CommandExecutionException) as e:
                self.logger.warning("Error while deleting {}: {}".format(item, e))

    def cleanup(self):
        self._cleanup_test_objects(self.users)
        self._cleanup_test_objects(self.invitations)
        transfer_titles = [t.title for t in self.transfers]
        if len(transfer_titles) > 0:
            data_sets = DataSet.api_get_matching_to_transfer_list(transfer_titles)
            self._cleanup_test_objects(data_sets)
            self._cleanup_test_objects(self.transfers)
        self._cleanup_test_objects(self.apps)
        self._cleanup_test_objects(self.service_instances)
        self._cleanup_test_objects(self.bindings)
        self._cleanup_test_objects(self.service_offerings)
        self._cleanup_test_objects(self.orgs)

        # TAP NG
        self._cleanup_test_objects(self.templates)
        self._cleanup_test_objects(self.catalog)
        self._cleanup_test_objects(self.blob_store)
        self._cleanup_test_objects(self.image_factory)
        self._cleanup_test_objects(self.k8s_apps)
        self._cleanup_test_objects(self.models)
        self._cleanup_test_objects(self.cli_applications)
        self._cleanup_test_objects(self.cli_offerings)
        self._cleanup_test_objects(self.cli_services)


@pytest.fixture(scope="function")
def context(request):
    context = Context()
    request.addfinalizer(context.cleanup)
    return context


@pytest.fixture(scope="class")
def class_context(request):
    context = Context()
    request.addfinalizer(context.cleanup)
    return context


@pytest.fixture(scope="module")
def module_context(request):
    context = Context()
    request.addfinalizer(context.cleanup)
    return context


@pytest.fixture(scope="session")
def session_context(request):
    context = Context()
    request.addfinalizer(context.cleanup)
    return context
