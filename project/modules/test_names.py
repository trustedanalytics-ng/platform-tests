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
import uuid
from datetime import datetime

import config


def is_test_object_name(name):
    """Return True if object's name matches pattern for test names, False otherwise."""
    if name is None:
        return False  # there are users with username=None
    test_name_regex = r'^.*[0-9]{8}(.?)[0-9]{6}\1([a-z0-9]{0,32}|([0-9]{6})?@gmail.com)?$'
    return re.match(test_name_regex, name) is not None


def generate_test_object_name(email=False, short=False, prefix=None, separator="_"):
    """Return string with hostname/prefix and date for use as name of test org, user, transfer, etc.
       Long version: ubuntuit_dp2_06_20160822_131159_728113.
       Short version: ubuntuitdp20620160822131159
    """
    # TODO add global counter
    date_format, time_format, ms_format = "%Y%m%d", "%H%M%S", "%f"
    now = datetime.now()
    date, time = now.strftime(date_format), now.strftime(time_format)
    milliseconds = "" if short else now.strftime(ms_format)
    guid = "" if short else str(uuid.uuid4()).replace("-", "")
    separator = "" if short else separator
    if prefix is None:
        prefix = socket.gethostname().split(".", 1)[0].replace("-", separator).lower()
    if email:
        email_format = config.test_user_email.replace('@', '+{}@')
        name = separator.join([prefix, date, time, milliseconds])
        return email_format.format(name)
    else:
        return separator.join([prefix, date, time, guid])


def escape_hive_name(string):
    escaped_chars = ",./<>?;':\"\|}{[]~`!@#$%^&*()_+-="
    return "".join([c if c not in escaped_chars else "_" for c in string])


def decode_org_id(org_guid):
    return org_guid.replace("-", "").decode("hex").rstrip("\x00")
