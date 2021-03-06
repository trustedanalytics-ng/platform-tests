#
# Copyright (c) 2017 Intel Corporation
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

from retry import retry

from modules.exceptions import UnexpectedResponseError
from ._cli_object_superclass import CliObjectSuperclass


class CliBinding(CliObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["type", "name", "direction_param", "src_name", "dst_name"]
    FIELD_NAME = "BINDING NAME"

    def __init__(self, *, tap_cli, type, name, src_name=None, dst_name=None):
        super().__init__(tap_cli=tap_cli, name=name)
        assert src_name is None or dst_name is None, "Test tried to bind with both src_name, dst_name!"
        assert src_name is not None or dst_name is not None, "Test tried to bind without src_name nor dst_name!"
        self.type = type
        self.name = name
        self.direction_param = self._get_direction_param(src_name, dst_name)
        self.src_name, self.dst_name = self._evaluate_src_and_dst(name, src_name, dst_name)

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.name < other.name

    @classmethod
    def create(cls, context, *, tap_cli, type, name, src_name=None, dst_name=None):
        binding = cls(tap_cli=tap_cli, type=type, name=name, src_name=src_name, dst_name=dst_name)
        tap_cli.bind(type, [tap_cli.NAME_PARAM, name] + binding.direction_param)
        context.test_objects.append(binding)
        return binding

    def delete(self):
        if self._is_deleted is True:
            return

        try:
            self.tap_cli.unbind(self.type, [self.tap_cli.NAME_PARAM, self.name] + self.direction_param)
            self._set_deleted(True)
        except UnexpectedResponseError:
            raise

    @retry(AssertionError, tries=12, delay=10)
    def ensure_on_bindings_list(self):
        app = next((b for b in self._get_bindings(self.dst_name) if b[self.FIELD_NAME] == self.src_name), None)
        assert app is not None, "Binding '{}' is not on the list of bindings".format(self.src_name)

    @retry(AssertionError, tries=12, delay=10)
    def ensure_not_on_bindings_list(self):
        app = next((b for b in self._get_bindings(self.dst_name) if b[self.FIELD_NAME] == self.src_name), None)
        assert app is None, "Binding '{}' is still on the list of bindings".format(self.src_name)

    def _get_direction_param(self, src_name, dst_name):
        if src_name is not None:
            return [self.tap_cli.SRC_NAME_PARAM, src_name]
        return [self.tap_cli.DST_NAME_PARAM, dst_name]

    def _get_bindings(self, name):
        return self.tap_cli.bindings(self.type, name, self.tap_cli.IS_DST_PARAM)

    @staticmethod
    def _evaluate_src_and_dst(name, src, dst):
        src_name = src
        dst_name = name
        if dst is not None:
            src_name = name
            dst_name = dst
        return src_name, dst_name