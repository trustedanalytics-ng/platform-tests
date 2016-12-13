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
from retry import retry

from modules.http_calls import hue


class Hive(object):
    def __init__(self, username=None, password=None):
        self.hue_client = hue.get_logged_client(username, password)

    def exec_query(self, query, database="default"):
        execute_response = hue.query_execute(database, query, self.hue_client)
        assert execute_response["status"] == 0

        self._wait_for_query(execute_response["id"])

        result_response = hue.query_result(execute_response["id"], self.hue_client)
        assert result_response["error"] == False

        return result_response["results"]

    @retry(AssertionError, tries=10, delay=3)
    def _wait_for_query(self, id):
        watch_response = hue.query_watch(id, self.hue_client)
        if watch_response["status"] != 0:
            raise ValueError("Bad status: {}".format(watch_response["status"]))
        assert watch_response["isFailure"] == False and watch_response["isSuccess"] == True
