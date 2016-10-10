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

from modules.constants import Path


class RunType:
    _API_SMOKE = "api-smoke"
    _API_FUNCTIONAL = "api-functional"
    _API_COMPONENTS = "api-components"
    _API_OTHER = "api-other"

    _PATH_TYPE_MAPPING = {
        Path.test_directories["test_functional"]: _API_FUNCTIONAL,
        Path.test_directories["test_smoke"]: _API_SMOKE,
        Path.test_directories["test_components"]: _API_COMPONENTS
    }

    @classmethod
    def get(cls, path_list):
        """
        Return test run type keyword based on the file/directory pytest parameter.
        """
        return cls._map_path(path_list[0]) if len(path_list) == 1 else cls._API_OTHER

    @classmethod
    def _map_path(cls, path):
        for test_dir_path, test_run_tag in cls._PATH_TYPE_MAPPING.items():
            if test_dir_path in path:
                return test_run_tag
        return cls._API_OTHER
