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

import argparse

from modules.runner.stats import log_all_stats, TEST_PATHS


def parse_args():
    parser = argparse.ArgumentParser(description="Tests statistics")
    parser.add_argument("-p", "--show-priorities",
                        help="show statistics according to priorities",
                        action="store_true")
    parser.add_argument("-c", "--show-components",
                        help="show statistics according to components",
                        action="store_true")
    parser.add_argument("-d", "--directory",
                        help="show statistics only in passed directory",
                        choices=TEST_PATHS,
                        default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    log_all_stats(**vars(args))
