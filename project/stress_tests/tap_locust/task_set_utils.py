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


class PytestSelector(str):
    def __new__(cls, module_path: str = None, class_name: str = None, test_name: str = None):
        pytest_selector = [s for s in (module_path, class_name, test_name) if s is not None]
        return str.__new__(cls, "::".join(pytest_selector))


def tasks_from_parametrized_test(pytest_selector, params):
    return [_gen_task(pytest_selector, param_set) for param_set in params]


def _gen_task(pytest_selector, params):
    params = _gen_param_string(params)
    pytest_params = ["--only-with-param", params]
    name = "{} {}".format(pytest_selector, params)

    def func(task_set_instance):
        task_set_instance.client.run(pytest_selector=pytest_selector, pytest_params=pytest_params, name=name)
    return func


def _gen_param_string(params):
    params = (str(arg) for arg in params)
    params = "-".join(params)
    return "[{}]".format(params)
