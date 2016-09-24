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

from modules.constants import Path
from modules.mongo_reporter._run_type import RunType


class TestRunType:

    @pytest.mark.parametrize("pytest_directory_arg,expected_run_type",
                             [(Path.test_directories["test_functional"], RunType._API_FUNCTIONAL),
                              (Path.test_directories["test_functional"] + "/kitten", RunType._API_FUNCTIONAL),
                              (Path.test_directories["test_smoke"], RunType._API_SMOKE),
                              (Path.test_directories["test_components"], RunType._API_COMPONENTS),
                              (Path.test_root_directory, RunType._API_OTHER),
                              ("kitten", RunType._API_OTHER)])
    def test_get(self, pytest_directory_arg, expected_run_type):
        run_type = RunType.get(pytest_directory_arg)
        assert run_type == expected_run_type
