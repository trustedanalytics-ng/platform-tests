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
import itertools
import pytest

import config
from modules.tap_logger import step
from modules.test_names import generate_test_object_name, is_test_object_name

ARGUMENT_COMBINATIONS = list(itertools.product(
    [True, False],  # email
    [True, False],  # short
    [None, 'PREFIX', '', ' '],  # prefix
    ['_', ':', '', ' ', '--'],  # separator
))
IDS = ['email={} short={} prefix={} separator={}'.format(*c) for c in ARGUMENT_COMBINATIONS]


class TestIsTestObjectName:

    @pytest.mark.parametrize('args_combination', ARGUMENT_COMBINATIONS, ids=IDS)
    def test_positive_cases(self, args_combination):
        name = generate_test_object_name(*args_combination)
        step('Testing if {} is recognized as test object name'.format(name))
        assert is_test_object_name(name)

    @pytest.mark.parametrize('args_combination', ARGUMENT_COMBINATIONS, ids=IDS)
    def test_positive_cases_with_unique_id(self, args_combination):
        config.unique_id = '1'
        name = generate_test_object_name(*args_combination)
        step('Testing if {} is recognized as test object name'.format(name))
        assert is_test_object_name(name)

    @pytest.mark.parametrize('name', [
        'review-sprint',
        'space-shuttle-demo',
        'test002',
        'space-shuttle-db',
        'PREFIX20161207:103732_408979',
        'taptester',
        'admin',
        '',
        ' '
    ])
    def test_negative_cases(self, name):
        step('Testing if {} is recognized as test object name'.format(name))
        assert not is_test_object_name(name)
