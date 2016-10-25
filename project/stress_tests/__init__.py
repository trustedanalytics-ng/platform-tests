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
import sys
from locust import events

from stress_tests.tap_locust.failed_stats import log_on_test_fail, print_failed_tests_stats


project_path = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(project_path)


events.request_failure += log_on_test_fail
events.quitting += print_failed_tests_stats
