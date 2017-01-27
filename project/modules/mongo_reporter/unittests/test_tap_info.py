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
from mock import mock
import pytest

from modules.mongo_reporter._tap_info import TapInfo


class MockConfig:
    tap_build_number = 4367


class TestTapInfo:

    @pytest.fixture
    def platform_info(self, monkeypatch):
        mock_platform_info = mock.Mock()
        mock_platform_info.return_value = mock_platform_info
        monkeypatch.setattr("modules.mongo_reporter._tap_info.PlatformInfo", mock_platform_info)
        return mock_platform_info

    def test_build_number_from_platform_version(self):
        assert 1235 == TapInfo._build_number_from_platform_version("0.8.1235")

    def test_get_build_number_when_platform_unreachable_and_no_env(self, platform_info):
        platform_info.get.side_effect = Exception
        assert TapInfo.get_build_number() is None

    @mock.patch("modules.mongo_reporter._tap_info.config", MockConfig)
    def test_get_build_number_when_platform_unreachable_and_env(self, platform_info):
        platform_info.get.side_effect = Exception
        assert MockConfig.tap_build_number == TapInfo.get_build_number()

    def test_get_build_number_when_platform_ok_and_not_config_env_set(self, platform_info):
        platform_info.get = platform_info
        platform_info.platform_version = "0.8.5641"
        assert 5641 == TapInfo.get_build_number()

    @mock.patch("modules.mongo_reporter._tap_info.config", MockConfig)
    def test_get_build_number_when_platform_ok_and_config_env_set(self, platform_info):
        platform_info.get = platform_info
        platform_info.platform_version = "0.8.5641"
        assert MockConfig.tap_build_number == TapInfo.get_build_number()

