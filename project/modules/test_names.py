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

import re
import socket
from datetime import datetime

import config


class TapObjectName:
    _date_format, _time_format, _ms_format = "%Y%m%d", "%H%M%S", "%f"
    _NON_ALPHA_NUM = r'[^a-z0-9]+'

    def __init__(self, short=False, prefix=None, separator='_'):
        self._prefix = prefix if prefix else socket.gethostname().split(".", 1)[0].lower()
        self._separator = separator
        self._short = short
        self._now = datetime.now()

    def __str__(self):
        separator = '' if self._short else self._separator
        parts = [self._prefix] + self.stem
        name = separator.join(parts).lower()
        return re.sub(self._NON_ALPHA_NUM, separator, name)

    @property
    def stem(self) -> list:
        seed = [
            self._now.strftime(self._date_format),
            self._now.strftime(self._time_format),
            self._now.strftime(self._ms_format)
        ]

        if config.unique_id:
            seed[-1] = '{:0>6}'.format(config.unique_id)

        return seed[:2] if self._short else seed

    def build(self) -> str:
        return str(self)

    def as_email(self) -> str:
        email_format = config.test_user_email.replace('@', '+{}@')
        email = email_format.format(self.build())
        if len(email.split("@")[0]) > 64:
            email = self.shorten_email_address(email)
        return email

    def shorten_email_address(self, email) -> str:
        year_month = self._now.strftime("%Y%m")
        return email.replace(year_month, "")


def is_test_object_name(name):
    """Return True if object's name matches pattern for test names, False otherwise."""
    if name is None:
        return False  # there are users with username=None
    test_name_regex = r'^.*[0-9]{2,8}(.*)[0-9]{6}\1([0-9]{6,})?(@gmail.com)?$'
    return re.match(test_name_regex, name) is not None


def generate_test_object_name(email=False, short=False, prefix=None, separator="_"):
    # TODO add global counter
    name = TapObjectName(short=short, prefix=prefix, separator=separator)
    return name.as_email() if email else name.build()


def escape_hive_name(string):
    escaped_chars = ",./<>?;':\"\|}{[]~`!@#$%^&*()_+-="
    return "".join([c if c not in escaped_chars else "_" for c in string])
