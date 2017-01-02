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
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
from time import sleep

import requests
from retry import retry

sys.path.insert(0, os.getcwd())

import config
from modules.command import run
from modules.constants import ApplicationPath
from modules.mongo_reporter.performance_reporter import PerformanceReporter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def setup():
    logger.info('Building sample apps')
    for app_dir in [ApplicationPath.SAMPLE_JAVA_APP, ApplicationPath.SAMPLE_PYTHON_APP, ApplicationPath.SAMPLE_GO_APP]:
        run(['./build.sh'], cwd=app_dir)


def teardown():
    pass


def start_locust_process(stress_run_id=None):
    command = ["locust", "-P", config.locust_port, "-f", config.locust_file]
    if stress_run_id is not None:
        os.environ.update({"PT_STRESS_RUN_ID": str(stress_run_id)})
    process = subprocess.Popen(command, universal_newlines=True)
    return process


@retry(tries=3, delay=1)
def start_test():
    response = requests.post("{}/swarm".format(config.locust_address),
                             data={'locust_count': config.num_clients, 'hatch_rate': config.hatch_rate})
    logger.info("/swarm response: {}".format(response))
    return response


def stop_test():
    response = requests.get("{}/stop".format(config.locust_address))
    logger.info("/stop response: {}".format(response))
    return response


def get_stats():
    response = requests.get("{}/stats/requests".format(config.locust_address))
    logger.info("/stats/requests response: {}".format(response))
    return json.loads(response.text)


try:
    setup()
    perf_mongo_reporter = PerformanceReporter()
    perf_mongo_reporter.start_gathering_metrics()
    locust_process = None
    try:
        locust_process = start_locust_process(stress_run_id=perf_mongo_reporter._run_id)
        start_test()
        sleep(config.test_duration)
    except:
        raise
    finally:
        stop_test()
        stats = get_stats()
        perf_mongo_reporter.on_run_end(stats)
        perf_mongo_reporter.stop_gathering_metrics()
        if locust_process is not None:
            locust_process.send_signal(signal.SIGTERM)
finally:
    teardown()

