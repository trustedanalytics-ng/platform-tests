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

from configuration import config
from modules.hive import Hive
from modules.tap_logger import get_logger
from modules.tap_object_model import DataSet, Invitation, Organization, Transfer, User
from modules.test_names import is_test_object_name
from tests.fixtures import fixtures

logger = get_logger(__name__)


def log_deleted_objects(object_list, object_type_name):
    if len(object_list) == 0:
        logger.info("No {}s to delete".format(object_type_name))
    else:
        logger.info("Deleting {} {}{}:\n{}".format(len(object_list), object_type_name,
                                                   "s" if len(object_list) != 1 else "",
                                                   "\n".join([str(x) for x in object_list])))


def remove_hive_databases():
    hive = Hive()
    dbs = hive.exec_query("show databases;")
    dbs = filter(lambda name: is_test_object_name(name), dbs)
    dbs = list(dbs)

    if dbs:
        logger.info("Removing databases:\n{}".format("\n".join(dbs)))
        dbs = map(lambda name: "DROP DATABASE {} CASCADE;".format(name), dbs)
        dbs = "".join(dbs)
        hive.exec_query(dbs)
    else:
        logger.info("No database to remove.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup script")
    parser.add_argument("-e",
                        "--environment",
                        default=None,
                        help="environment where tests are to be run, e.g. daily.gotapaas.com")
    parser.add_argument("-l", "--logging-level",
                        choices=["DEBUG", "INFO", "WARNING"],
                        default="DEBUG")
    args = parser.parse_args()
    config.update_test_config(domain=args.environment, logging_level=args.logging_level)

    all_data_sets = DataSet.api_get_list()
    test_data_sets = [x for x in all_data_sets if is_test_object_name(x.title)]
    log_deleted_objects(test_data_sets, "data set")
    fixtures.tear_down_test_objects(test_data_sets)

    all_transfers = Transfer.api_get_list()
    test_transfers = [x for x in all_transfers if is_test_object_name(x.title)]
    log_deleted_objects(test_transfers, "transfer")
    fixtures.tear_down_test_objects(test_transfers)

    all_users = User.cf_api_get_all_users()
    test_users = [x for x in all_users if is_test_object_name(x.username)]
    log_deleted_objects(test_users, "user")
    fixtures.tear_down_test_objects(test_users)

    all_pending_invitations = Invitation.api_get_list()
    test_invitations = [x for x in all_pending_invitations if is_test_object_name(x.username)]
    log_deleted_objects(test_invitations, "invitation")
    fixtures.tear_down_test_objects(test_invitations)

    all_orgs = Organization.cf_api_get_list()
    test_orgs = [x for x in all_orgs if is_test_object_name(x.name)]
    log_deleted_objects(test_orgs, "organization")
    fixtures.tear_down_test_objects(test_orgs,)

    remove_hive_databases()

