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

from common import parse_arguments, check_uaa_file

parameters = parse_arguments()

directory = os.path.dirname(__file__)

uaa_file_name = os.path.join(directory, parameters.uaa_file_name)
ta.create_credentials_file(uaa_file_name)

check_uaa_file(uaa_file_name)

hdfs_csv_path = parameters.target_uri
schema = [('doc_id', str), ('word_id', str), ('word_count', ta.int64)]
csv_file = ta.CsvFile(hdfs_csv_path, schema)
frame = ta.Frame(csv_file)
model = ta.LdaModel()
model.train(frame, 'doc_id', 'word_id', 'word_count', max_iterations=3, num_topics=2)
print("hdfs_model_path: " + model.publish())
