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

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file

parameters = parse_arguments()

ta.create_credentials_file(parameters.uaa_file_name)

check_uaa_file(parameters.uaa_file_name)

query_select = "SELECT * FROM " + parameters.organization + "." + parameters.transfer
print("Query: {}".format(query_select))
hq = ta.HiveQuery(query_select)
frame_select = ta.Frame(hq)

column_names_list = frame_select.column_names
column_names_len = len(column_names_list)

print("\n------------ Test: group_by method ------------")
frame_group = frame_select.group_by(column_names_list[0], ta.agg.count)
frame_group_content = frame_group.inspect()
print("frame_group_content: ", frame_group_content)

frame_group_columns_list = frame_group.column_names
frame_group_columns_len = len(frame_group_columns_list)

if frame_group_columns_len == 2 and frame_group_columns_list[0] == column_names_list[0] and \
                frame_group_columns_list[1] == 'count':
    print("Table {} grouped correctly".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Table {} was NOT grouped correctly".format(parameters.organization + "." +
                                                                       parameters.transfer))

print("\n------------ Test: add_column method ------------")
frame_select.add_columns(lambda row: "", ("test_column", str))

frame_add_columns_list = frame_select.column_names
frame_add_columns_len = len(frame_add_columns_list)

if frame_add_columns_len == (column_names_len+1) and frame_add_columns_list[column_names_len] == "test_column":
    print("Column was added to table {}".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Column was NOT added to table {}".format(parameters.organization + "." +
                                                                       parameters.transfer))

print("\n------------ Test: drop_column method ------------")
frame_select.drop_columns('test_column')

frame_drop_columns_list = frame_select.column_names
frame_drop_columns_len = len(frame_drop_columns_list)

if frame_drop_columns_len == column_names_len and 'test_column' not in frame_drop_columns_list:
    print("Column 'test_column' was dropped in table {}".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Column was NOT dropped in table {}".format(parameters.organization + "." +
                                                                       parameters.transfer))

print("\n------------ Test: drop_frames method ----------------")
ta.drop_frames([frame_select, frame_group])
if frame_select.status != 'Active' and frame_group.status != 'Active':
    print("Frames {}, {} removed successfully".format(frame_select, frame_group))
else:
    raise AtkTestException("Frames {}, {} NOT deleted. Status of both frames should be Deleted ".format(frame_select,
                                                                                                        frame_group))
