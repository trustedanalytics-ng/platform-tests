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


class Path:
    test_root_directory = os.path.join("tests")
    test_directories = {
        "test_functional": os.path.join(test_root_directory, "test_functional"),
        "test_smoke": os.path.join(test_root_directory, "test_smoke"),
        "test_monitoring": os.path.join(test_root_directory, "test_monitoring"),
        "test_performance": os.path.join(test_root_directory, "test_performance"),
    }
