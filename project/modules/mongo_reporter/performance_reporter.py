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

from apscheduler.schedulers.background import BackgroundScheduler

import config
from modules.mongo_reporter.base_reporter import BaseReporter
from modules.tap_logger import step
from modules.tap_object_model import Metrics


class PerformanceReporter(BaseReporter):

    _TEST_RUN_COLLECTION_NAME = "performance_test_run"
    METRICS_INTERVAL = 10
    REQUIRED_METRICS = ['timestamp', 'cpu_usage_platform', 'memory_usage_platform']
    scheduler = None
    metrics_job = None

    def __init__(self, *args, **kwargs):
        mongo_run_document = {
            "end_date": None,
            "environment": config.tap_domain,
            "environment_version": config.tap_version,
            "finished": False,
            "hatch_rate": config.hatch_rate,
            "infrastructure_type": config.tap_infrastructure_type,
            "metrics": [],
            "number_of_users": config.num_clients,
            "start_date": datetime.now(),
            "started by": socket.gethostname(),
            "status": self._RESULT_UNKNOWN,
        }
        super().__init__(mongo_run_document, *args, **kwargs)
        self.scheduler = BackgroundScheduler()

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

    def start_gathering_metrics(self):
        if config.log_metrics_interval > 0:
            print('start gathering metrics')
            self.metrics_job = self.scheduler.add_job(self._get_metrics, 'interval',
                                                      seconds=config.log_metrics_interval)
            self.scheduler.start()

    def stop_gathering_metrics(self):
        if config.log_metrics_interval > 0:
            print('stop gathering metrics')
            if self.metrics_job:
                self.metrics_job.remove()

    def _get_metrics(self):
        print('Getting metrics from Grafana')
        metrics = Metrics.from_grafana(metrics_level='platform')
        metrics = vars(metrics)
        log = 'Metrics: time: {timestamp} cpu: {cpu_usage_platform}% memory: {memory_usage_platform}GB'
        step(log.format(**metrics))
        required_metrics = {k: metrics[k] for k in self.REQUIRED_METRICS}
        self._update_metrics(required_metrics)

    def _update_metrics(self, metrics):
        self._mongo_run_document['metrics'].append(metrics)
        self._save_test_run()

