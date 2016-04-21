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

import argparse

from configuration import config
from modules.exceptions import UnexpectedResponseError
from modules.hive import Hive
from modules.tap_logger import get_logger
from modules.tap_object_model import DataSet, Organization, Transfer, User
from modules.test_names import is_test_object_name


logger = get_logger(__name__)


def delete_test_objects(object_list, object_type_name, delete_method_name=None, delete_method=None):
    if len(object_list) == 0:
        logger.info("No {}s to delete".format(object_type_name))
    else:
        logger.info("Deleting {} {}{}:\n{}".format(len(object_list), object_type_name,
                                                   "s" if len(object_list) != 1 else "",
                                                   "\n".join([str(x) for x in object_list])))
        failed_to_delete = []
        for o in object_list:
            try:
                if delete_method_name is not None:
                    getattr(o, delete_method_name)()
                else:
                    delete_method(o)
            except UnexpectedResponseError as e:
                failed_to_delete.append(o)
                logger.warning("Failed to delete {}: {}".format(o, e))
        if len(failed_to_delete) > 0:
            logger.info("Failed to delete {} {}{}:\n{}".format(len(failed_to_delete), object_type_name,
                                                               "s" if len(object_list) != 1 else "",
                                                               "\n".join([str(x) for x in failed_to_delete])))
    logger.info("=" * 100)


def remove_hive_databases():
    with Hive() as hive:
        dbs = hive.exec_query("show databases;").split("\n")
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

    parser = argparse.ArgumentParser(description="Test org cleanup script")
    parser.add_argument("-e",
                        "--environment",
                        default=None,
                        help="environment where tests are to be run, e.g. daily.gotapaas.com")
    parser.add_argument("-l", "--logging-level",
                        choices=["DEBUG", "INFO", "WARNING"],
                        default="INFO")
    args = parser.parse_args()
    config.update_test_config(domain=args.environment, logging_level=args.logging_level)

    all_orgs = Organization.cf_api_get_list()
    test_orgs = [x for x in all_orgs if is_test_object_name(x.name)]
    all_data_sets = DataSet.api_get_list(org_list=all_orgs)
    test_data_sets = [x for x in all_data_sets if is_test_object_name(x.title)]
    all_transfers = Transfer.api_get_list(org_guid_list=[org.guid for org in all_orgs])
    test_transfers = [x for x in all_transfers if is_test_object_name(x.title)]
    all_users = User.cf_api_get_all_users()
    test_users = [x for x in all_users if is_test_object_name(x.username)]
    all_pending_invitations = User.api_get_pending_invitations()
    test_invitations = [x for x in all_pending_invitations if is_test_object_name(x)]

    delete_test_objects(test_data_sets, "data set", delete_method_name="api_delete")
    delete_test_objects(test_transfers, "transfer", delete_method_name="api_delete")
    delete_test_objects(test_users, "user", delete_method_name="cf_api_delete")
    delete_test_objects(test_invitations, "pending invitation", delete_method=User.api_delete_user_invitation)
    delete_test_objects(test_orgs, "organization", delete_method_name="cf_api_delete")
    remove_hive_databases()
