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
from collections import defaultdict
from statistics import mean, median

tests_times = defaultdict(list)


def log_on_test_fail(request_type, name, response_time, exception, **kwargs):
    tests_times[name].append(response_time)


def print_failed_tests_stats(**kwargs):
    print("Time stats for failed tests")
    template = "{:90} {:>10} {:>10} {:>10} {:>10}"
    print(template.format("Name", "avg", "min", "max", "median"))
    template = "{:90} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}"
    for name, times in sorted(tests_times.items()):
        print(template.format(name, mean(times), min(times), max(times), median(times)))
