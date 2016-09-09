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


class StreamCapture(object):

    def __init__(self, original_stream):
        self._original_stream = original_stream
        self._output = []

    def write(self, s):
        s = s.strip()
        if len(s) > 0:
            self._output.append(s.strip())

    def flush(self):
        pass

    def isatty(self):
        if hasattr(self._original_stream, "isatty"):
            return self._original_stream.isatty()
        return False

    @property
    def original_stream(self):
        return self._original_stream

    @property
    def output(self):
        output = "\n".join(self._output)
        return output
