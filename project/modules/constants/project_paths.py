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
        "test_components": os.path.join(test_root_directory, "test_components"),
        "test_functional": os.path.join(test_root_directory, "test_functional"),
        "test_smoke": os.path.join(test_root_directory, "test_smoke"),
        "test_monitoring": os.path.join(test_root_directory, "test_monitoring"),
        "test_performance": os.path.join(test_root_directory, "test_performance"),
        "stress_scenarios": os.path.join(test_root_directory, "stress_scenarios"),
        "test_system": os.path.join(test_root_directory, "test_system")
    }

    bumpversion_file = os.path.abspath(os.path.join("..", ".bumpversion.cfg"))
    fixture_root_dir = os.path.join("fixtures")
    mqtt_demo_certificate = os.path.join(fixture_root_dir, "mosquitto_demo_cret.pem")
    data_set_dir = os.path.join(fixture_root_dir, "data_sets")
    shuttle_csv_file = os.path.join(data_set_dir, "shuttle_scale_cut_val.csv")
    shuttle_csv_file_truncated = os.path.join(data_set_dir, "shuttle_scale_cut_val-truncated.csv")
    _2_kilobytes_csv_file = os.path.join(data_set_dir, "2_kilobytes.csv")