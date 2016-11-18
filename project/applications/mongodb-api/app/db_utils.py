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
import logging

from bson.objectid import ObjectId
from pymongo import MongoClient
from retry import retry

from config import Config

logger = logging.getLogger(__name__)


class DatabaseClient(object):
    def __init__(self):
        self.config = Config()
        self.connection = MongoClient(self.config.db_hostname, port=self.config.db_port)
        self._database = self.connection[self.config.db_name]
        if self.config.db_username and self.config.db_password:
            self._database.authenticate(self.config.db_username, self.config.db_password)

    def add_member_to_replica(self, hostport, config, arbiter=False):
        config["version"] += 1
        max_id = max([config["members"][i]["_id"] for i in range(len(config["members"]))])
        hostport_config = hostport
        if isinstance(hostport, str):
            hostport_config = {
                "_id": max_id + 1,
                "host": hostport
            }
            if arbiter:
                hostport_config["arbiterOnly"] = True
        elif arbiter:
            raise Exception("Expected first parameter to be a host-and-port string of arbiter, but got '{}'".
                            format(hostport))
        if hostport_config["_id"] is None:
            hostport_config["_id"] = max_id + 1
        if str(hostport_config["host"]) not in str(config["members"]):
            config["members"].append(hostport_config)
        return self._database.command("replSetReconfig", config)

    @retry(AssertionError, tries=30, delay=10)
    def configure_mongo_cluster(self):
        try:
            self._database.command("replSetInitiate")
        except Exception as e:
            logger.error(e)
        assert self.connection.local.system.replset.count() <= 1, "Error: local.system.replset has unexpected contents"
        config = self.connection.local.system.replset.find_one()
        assert config, "No config object retrievable from local.system.replset"
        config["members"][0]["host"] = "{}:{}".format(self.config.db_hostname0, self.config.db_port0)
        try:
            self._database.command("replSetReconfig", config)
        except Exception as e:
            logger.error(e)
        self.add_member_to_replica("{}:{}".format(self.config.db_hostname1, self.config.db_port1), config)
        self.add_member_to_replica("{}:{}".format(self.config.db_hostname2, self.config.db_port2), config)
        status = str(self._database.command("replSetGetStatus"))
        assert "PRIMARY" in status and "SECONDARY" in status, "Configuration status is incorrect"

    def get_collection_list(self):
        return self._database.collection_names()

    def add_collection(self, collection_name):
        self._database.create_collection(collection_name)

    def delete_collection(self, collection_name):
        self._database.drop_collection(collection_name)

    def get_documents(self, collection_name):
        result = self._database[collection_name].find({})
        return list(result)

    def add_document(self, collection_name, new_data):
        result = self._database[collection_name].insert_one(new_data)
        return str(result.inserted_id)

    def replace_document(self, collection_name, document_id, new_data):
        self._database[collection_name].replace_one({"_id": ObjectId(document_id)}, new_data)

    def delete_document(self, collection_name, document_id):
        self._database[collection_name].delete_one({"_id": ObjectId(document_id)})
