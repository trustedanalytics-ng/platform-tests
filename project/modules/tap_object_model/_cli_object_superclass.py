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

import functools


@functools.total_ordering
class CliObjectSuperclass(object):
    _COMPARABLE_ATTRIBUTES = None

    def __init__(self, *, tap_cli, name):
        self.tap_cli = tap_cli
        self.name = name

    def __eq__(self, other):
        if self._COMPARABLE_ATTRIBUTES is None:
            raise NotImplementedError("_COMPARABLE_ATTRIBUTES not implemented for class {}".format(self.__class__.__name__))
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self._COMPARABLE_ATTRIBUTES))

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    def delete(self):
        raise NotImplemented

    def cleanup(self):
        self.delete()
