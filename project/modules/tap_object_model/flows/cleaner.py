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

from modules.exceptions import UnexpectedResponseError
from modules.tap_logger import get_logger
from modules.tap_object_model import DataSet, Invitation, Organization, Transfer, User


logger = get_logger(__name__)


def tear_down_test_objects(object_list: list, delete_method_name: str):
    for item in object_list:
        try:
            getattr(item, delete_method_name)()
        except UnexpectedResponseError as e:
            logger.warning("Failed to delete {}: {}".format(item, e))


def tear_down_test_data_catalog_items():
    """Delete all test transfers and data sets"""
    transfer_titles = Transfer.TEST_TRANSFER_TITLES
    if len(transfer_titles) > 0:
        transfers = Transfer.api_get_list()
        test_transfers = [t for t in transfers if t.title in transfer_titles]
        tear_down_test_objects(object_list=test_transfers, delete_method_name="api_delete")
        data_sets = DataSet.api_get_list()
        test_data_sets = [d for d in data_sets if d.title in transfer_titles]
        tear_down_test_objects(object_list=test_data_sets, delete_method_name="api_delete")


def tear_down_test_orgs():
    org_names = Organization.TEST_ORG_NAMES
    if len(org_names) > 0:
        organizations = Organization.cf_api_get_list()
        test_orgs = [o for o in organizations if o.name in org_names]
        tear_down_test_objects(object_list=test_orgs, delete_method_name="cf_api_delete")


def tear_down_test_users_and_invites():
    user_names = User.TEST_USERNAMES
    if len(user_names) > 0:
        users = User.cf_api_get_all_users()
        test_users = [u for u in users if u.username in user_names]
        tear_down_test_objects(object_list=test_users, delete_method_name="cf_api_delete")
        invites = Invitation.api_get_list()
        test_invites = [i for i in invites if i.username in user_names]
        tear_down_test_objects(object_list=test_invites, delete_method_name="api_delete")


def tear_down_all():
    tear_down_test_data_catalog_items()
    tear_down_test_users_and_invites()
    tear_down_test_orgs()
