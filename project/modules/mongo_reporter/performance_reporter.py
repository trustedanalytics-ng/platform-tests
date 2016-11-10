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
import socket
from datetime import datetime

import config
from modules.mongo_reporter.base_reporter import BaseReporter


class PerformanceReporter(BaseReporter):

    _TEST_RUN_COLLECTION_NAME = "performance_test_run"

    def __init__(self, *args, **kwargs):
        mongo_run_document = {
            "end_date": None,
            "environment": config.tap_domain,
            "environment_version": config.tap_version,
            "finished": False,
            "hatch_rate": config.hatch_rate,
            "infrastructure_type": config.tap_infrastructure_type,
            "number_of_users": config.num_clients,
            "start_date": datetime.now(),
            "started by": socket.gethostname(),
            "status": self._RESULT_UNKNOWN,
        }
        super().__init__(mongo_run_document, *args, **kwargs)

    def on_run_end(self, stats):
        mongo_performance_run_document = {
            "end_date": datetime.now(),
            "finished": True,
            "status": self._get_status(stats)
        }
        self._mongo_run_document.update(mongo_performance_run_document)
        self._save_test_run()

    @staticmethod
    def _get_status(stats):
        stats = stats["stats"]
        total_stats = stats[-1]
        return BaseReporter._RESULT_FAIL if int(total_stats["num_failures"]) else BaseReporter._RESULT_PASS
