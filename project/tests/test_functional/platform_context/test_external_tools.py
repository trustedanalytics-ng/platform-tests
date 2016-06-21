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

from modules.constants import TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import ExternalTools
from tests.fixtures.assertions import assert_no_errors

logged_components = (TAP.platform_context,)
pytestmark = [components.platform_context]


class TestExternalToolsStatus(object):

    tools_list = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def external_tools_list(cls):
        step("Get list of external tools")
        cls.tools_list = ExternalTools.api_get_external_tools()

    @priority.medium
    def test_external_tools_should_be_available(self):
        tools = [t for t in self.tools_list if t.should_have_url and t.url and t.available]
        errors = []
        for tool in tools:
            try:
                tool.send_request()
            except UnexpectedResponseError:
                errors.append("Tool '{}' failed to respond with OK status.".format(tool.name))
        assert_no_errors(errors)

    @priority.medium
    def test_external_tools_should_be_not_available_but_should_have_url(self):
        tools = [t for t in self.tools_list if t.should_have_url and t.url and not t.available]
        errors = []
        for tool in tools:
            try:
                tool.send_request()
            except UnexpectedResponseError:
                pass
            else:
                errors.append("Tool '{}' failed to respond with error status.".format(tool.name))
        assert_no_errors(errors)

    @priority.medium
    def test_external_tools_should_have_url(self):
        tools = [t for t in self.tools_list if t.should_have_url]
        errors = []
        for tool in tools:
            if tool.url is None:
                errors.append("Tool '{}' has no URL specified.".format(tool.name))
        assert_no_errors(errors)

    @priority.medium
    def test_external_tools_should_have_no_url(self):
        tools = [t for t in self.tools_list if not t.should_have_url]
        errors = []
        for tool in tools:
            if tool.url is not None:
                errors.append("Tool '{}' has URL specified.".format(tool.name))
        assert_no_errors(errors)
