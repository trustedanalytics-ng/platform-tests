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

from bson import ObjectId

import config
from modules.mongo_reporter._client import MockDbClient, DBClient

logger = logging.getLogger(__name__)


class BaseReporter(object):
    _RESULT_PASS = "PASS"
    _RESULT_FAIL = "FAIL"
    _RESULT_SKIPPED = "SKIPPED"
    _RESULT_UNKNOWN = "UNKNOWN"

    _TEST_RUN_COLLECTION_NAME = None

    def __init__(self, mongo_run_document, run_id=None):
        """Important! This method cannot make http calls!"""

        if config.database_url is None:
            logger.warning("Not writing results to a database - database_url not configured.")
            self._db_client = MockDbClient()
        else:
            self._db_client = DBClient(uri=config.database_url)

        if run_id is not None:
            run_id = ObjectId(run_id)
        self._run_id = run_id

        self._mongo_run_document = mongo_run_document
        self._save_test_run()

    def _save_test_run(self):
        assert self._TEST_RUN_COLLECTION_NAME is not None, "No collection name is provided to reporter"
        if self._run_id is None:
            self._run_id = self._db_client.insert(collection_name=self._TEST_RUN_COLLECTION_NAME,
                                                  document=self._mongo_run_document)
        else:
            self._db_client.replace(collection_name=self._TEST_RUN_COLLECTION_NAME, document_id=self._run_id,
                                    new_document=self._mongo_run_document)
