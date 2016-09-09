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
import os
import subprocess
from time import sleep

import requests
import signal

import sys
from retry import retry

project_path = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(project_path)

from config import get_int


locust_file = os.environ["PT_LOCUST_FILE"]
num_clients = os.environ.get("PT_NUM_CLIENTS", "2")
hatch_rate = os.environ.get("PT_HATCH_RATE", "1")
test_duration = get_int("PT_DURATION", 10) * 60
locust_port = os.environ.get("PT_LOCUST_PORT", "8089")
locust_address = "http://localhost:{}/".format(locust_port)


def start_locust_process(locust_file):
    command = ["locust", "-P", locust_port, "-f", locust_file]
    return subprocess.Popen(command, universal_newlines=True)


@retry(tries=3, delay=1)
def start_test(num_clients, hatch_rate):
    return requests.post("{}swarm".format(locust_address),
                         data={'locust_count': num_clients, 'hatch_rate': hatch_rate})


def stop_test():
    return requests.get("{}stop".format(locust_address))


def get_stats():
    return requests.get("{}requests".format(locust_address))


locust_process = None
try:
    locust_process = start_locust_process(locust_file)
    start_test(num_clients, hatch_rate)
    sleep(test_duration)
    stop_test()
    get_stats()
except:
    raise
finally:
    if locust_process is not None:
        locust_process.send_signal(signal.SIGINT)
