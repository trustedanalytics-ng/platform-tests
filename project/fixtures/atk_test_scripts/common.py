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

import argparse
import os
import re

import trustedanalytics as ta


class AtkTestException(AssertionError):
    pass


def parse_arguments():
    parser = argparse.ArgumentParser(description="ATK Python Client Test")
    parser.add_argument("--database-name",
                        help="Hive database name (org guid)")
    parser.add_argument("--table-name",
                        help="Hive table name (transfer title)")
    parser.add_argument("--uaa_file_name",
                        help="uaa file name that will be created by script")
    parser.add_argument("--target_uri",
                        help="hdfs storage address")
    return parser.parse_args()

def check_uaa_file(uaa_file_name):
    if not os.path.isfile(uaa_file_name):
        raise AtkTestException("authorization file not found")
    if os.stat(uaa_file_name).st_size == 0:
        raise AtkTestException("authorization file is empty")
    print("UAA file correctly created")

def remove_test_tables_from_database(database, test_table_pattern):
    query_show_tables = "SHOW TABLES IN " + database[0]
    print("\nQuery: {}".format(query_show_tables))
    hq_show_tables = ta.HiveQuery(query_show_tables)
    frame_show_tables = ta.Frame(hq_show_tables)
    frame_show_tables_content = frame_show_tables.inspect(n=50)
    tables_to_remove = frame_show_tables_content.rows
    if database[0] == "default":
        tables_to_remove = [row for row in tables_to_remove if re.match(test_table_pattern, row[0])]
    print("tables to remove: ", tables_to_remove)
    for tab in tables_to_remove:
        delete_tab_query = "DROP TABLE " + database[0] + "." + tab[0]
        print("Query: {}".format(delete_tab_query))
        hq_tab_delete = ta.HiveQuery(delete_tab_query)
        ta.Frame(hq_tab_delete)
    if database[0] != "default":
        delete_db_query = "DROP DATABASE " + database[0]
        print("Query: {}".format(delete_db_query))
        hq_db_delete = ta.HiveQuery(delete_db_query)
        ta.Frame(hq_db_delete)
