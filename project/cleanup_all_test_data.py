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
from modules.hive import Hive
from modules.tap_logger import get_logger
from modules.tap_object_model import DataSet, Invitation, Transfer, User, Application, ServiceInstance, \
    ServiceOffering, ScoringEngineModel
from modules.test_names import is_test_object_name
from tests.fixtures import fixtures
from tests.fixtures.fixtures import core_org

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


def _cleanup_test_data(name, objects_list, name_attribute):
    try:
        test_objects = []
        for test_object in objects_list:
            object_name = getattr(test_object, name_attribute)
            if is_test_object_name(object_name):
                test_objects.append(test_object)
        log_deleted_objects(test_objects, name)
        fixtures.tear_down_test_objects(test_objects)
    except UnexpectedResponseError as e:
        logger.error('Cannot cleanup {}s, reason: {}'.format(name, e))


def cleanup_test_data():
    core_org_guid = core_org().guid
    test_object_models = [
        {'name': 'data set', 'objects_list': DataSet.api_get_list(), 'name_attribute': 'title'},
        {'name': 'transfer', 'objects_list': Transfer.api_get_list(), 'name_attribute': 'title'},
        {'name': 'user', 'objects_list': User.get_list_in_organization(org_guid=core_org_guid), 'name_attribute': 'username'},
        {'name': 'invitation', 'objects_list': Invitation.api_get_list(), 'name_attribute': 'username'},
        {'name': 'application', 'objects_list': Application.get_list(), 'name_attribute': 'name'},
        {'name': 'service', 'objects_list': ServiceInstance.get_list(), 'name_attribute': 'name'},
        {'name': 'offering', 'objects_list': ServiceOffering.get_list(), 'name_attribute': 'label'},
        {'name': 'scoring engine model', 'objects_list': ScoringEngineModel.get_list(org_guid=core_org_guid),
         'name_attribute': 'name'}
    ]
    for model in test_object_models:
        _cleanup_test_data(**model)

    # TODO: remove hive dbs


if __name__ == "__main__":
    cleanup_test_data()
