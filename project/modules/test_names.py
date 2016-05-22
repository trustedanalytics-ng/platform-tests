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

from datetime import datetime
import re
import socket

import config


def is_test_object_name(name):
    """Return True if object's name matches pattern for test names, False otherwise."""
    if name is None:
        return False  # there are users with username=None
    test_name_regex = "^.+[0-9]{8}_[0-9]{6}_{0,1}[0-9]{0,6}(@gmail.com){0,1}$"
    return re.match(test_name_regex, name) is not None


def generate_test_object_name(email=False, short=False, prefix=None):
    """Return string with hostname/prefix and date for use as name of test org, user, transfer, etc."""
    # TODO add global counter
    str_format = "%Y%m%d_%H%M%S" if short else "%Y%m%d_%H%M%S_%f"
    now = datetime.now().strftime(str_format)
    name_format = config.test_user_email.replace('@', '+{}_{}@') if email else "{}_{}"
    if prefix is None:
        prefix = socket.gethostname().replace("-", "_").lower()
    return name_format.format(prefix, now)


def escape_hive_name(string):
    escaped_chars = ",./<>?;':\"\|}{[]~`!@#$%^&*()_+-="
    return "".join([c if c not in escaped_chars else "_" for c in string])
