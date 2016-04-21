#
# Copyright (c) 2015-2016 Intel Corporation
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

import os
import re

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file, remove_test_tables_from_database

TEST_PATTERN = "^.+[0-9]{8}_[0-9]{6}_{0,1}[0-9]{0,6}(@gmail.com){0,1}$"

parameters = parse_arguments()

directory = os.path.dirname(__file__)

ta.create_credentials_file(parameters.uaa_file_name)

check_uaa_file(parameters.uaa_file_name)

print("uaa file found")

query = "SHOW DATABASES"  # don't put semicolon at the end
print("\nQuery: {}".format(query))
hq = ta.HiveQuery(query)
frame = ta.Frame(hq)

frame_content = frame.inspect(n=50)  # returns 50 rows
frame_rows = frame_content.rows
databases_to_remove = [row for row in frame_rows if re.match(TEST_PATTERN, row[0])]
print(databases_to_remove)

for database in databases_to_remove:
    remove_test_tables_from_database(database, TEST_PATTERN)

remove_test_tables_from_database(["default"], TEST_PATTERN)




