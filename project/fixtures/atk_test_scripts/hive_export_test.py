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

import datetime

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file

parameters = parse_arguments()

ta.create_credentials_file(parameters.uaa_file_name)

check_uaa_file(parameters.uaa_file_name)

query_source = "select * from " + parameters.database_name + "." + parameters.table_name
print("Query: {}".format(query_source))
hq = ta.HiveQuery(query_source)
original_frame = ta.Frame(hq)

destination_table = "test_tab_{}".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))

print("exporting...")
original_frame.export_to_hive(destination_table)

query_destination = "select * from default." + destination_table
print("Query: {}".format(query_destination))
hq_default = ta.HiveQuery(query_destination)
exported_frame = ta.Frame(hq_default)

original_table_rows = original_frame.row_count
exported_table_rows = exported_frame.row_count

print("original_table_rows: ", original_table_rows)
print("exported_table_rows: ", exported_table_rows)

original_table_content = original_frame.inspect()
exported_table_content = exported_frame.inspect()

print("original_table_content: ", original_table_content)
print("exported_table_content: ", exported_table_content)

original_table_inspect_list = original_table_content.rows
exported_table_inspect_list = exported_table_content.rows

if original_table_rows == exported_table_rows and original_table_inspect_list == exported_table_inspect_list:
    print("Table {} exported correctly".format(parameters.database_name + "." + parameters.table_name))
else:
    raise AtkTestException("Exported data is not same to original one")

