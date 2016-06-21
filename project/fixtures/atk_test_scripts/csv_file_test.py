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

import os

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file


parameters = parse_arguments()

directory = os.path.dirname(__file__)

ta.create_credentials_file(parameters.uaa_file_name)

check_uaa_file(parameters.uaa_file_name)

hdfs_path = parameters.target_uri
print("Create CsvFile from hdfs data set")
hcsv = ta.CsvFile(hdfs_path, schema=[('line' + str(i), str) for i in xrange(8)], delimiter=",")
frame = ta.Frame(hcsv)

frame_content = frame.inspect(20)
print("original_table_content: ", frame_content)
frame_rows = frame_content.rows

if frame.row_count == 17:
    print("Frame of file {} created correctly".format(hdfs_path))
else:
    raise AtkTestException("Frame of file {} not created correctly".format(hdfs_path))
