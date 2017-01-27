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
import os
import signal
import subprocess
import sys
import time

import pytest
import _pytest.main as pytest_main
from locust import events

from stress_tests.tap_locust.task_set_utils import PytestSelector
from stress_tests.tap_locust.username_pool import UsernameLock
from ._stream_capture import StreamCapture

project_path = os.path.abspath(os.path.join(__file__, "..", "..", ".."))

logger = logging.getLogger(__name__)


class AtomicCounter:

    def __init__(self, start_with=0):
        self.value = start_with
        self.lock = logging.threading.Lock()

    def get_and_increment(self):
        with self.lock:
            v = self.value
            self.value += 1
        return v


class LocustClient(object):
    CAPTURE_PYTEST_OUTPUT = False

    counter = AtomicCounter()

    def capture_start(self):
        if self.CAPTURE_PYTEST_OUTPUT:
            logger.info("Capture start")
            self.out_capture = StreamCapture(sys.stdout)
            self.err_capture = StreamCapture(sys.stderr)
            sys.stdout = self.out_capture
            sys.stderr = self.err_capture

    def capture_end(self):
        if self.CAPTURE_PYTEST_OUTPUT:
            logger.info("Capture end")
            sys.stdout = self.out_capture.original_stream
            sys.stderr = self.err_capture.original_stream
            out = self.out_capture.output
            err = self.err_capture.output
            return out, err
        return "", ""

    def run(self, pytest_selector: PytestSelector, pytest_params: list=None, name: str=None):
        name = name or pytest_selector
        pytest_params = pytest_params or []

        logger.info("Starting pytest with {}".format(str([pytest_selector] + pytest_params)))
        ret_code, out, err, exec_time = self.run_pytest(pytest_selector, pytest_params)
        logger.info("Pytest exit with code: {}".format(ret_code))

        if ret_code == pytest_main.EXIT_OK:
            events.request_success.fire(request_type="test", name=name, response_time=exec_time,
                                        response_length=0)
        elif ret_code == pytest_main.EXIT_TESTSFAILED:
            events.request_failure.fire(request_type="test", name=name, response_time=exec_time,
                                        exception=out + err)

    def run_pytest(self, selector, params):
        with UsernameLock() as username:
            env = dict(os.environ)
            unique_id = str(self.counter.get_and_increment())
            env["PT_UNIQUE_ID"] = unique_id
            env["PT_PERF_ADMIN_USERNAME"] = username

            command = ["py.test", selector] + params

            process = None
            self.capture_start()
            try:
                start_time = time.time()
                process = subprocess.Popen(command, env=env, cwd=project_path, universal_newlines=True)
                process.wait()
                total_time = int((time.time() - start_time) * 1000)
            except:
                logger.warn("Terminating pytest")
                process.send_signal(signal.SIGINT)
                raise
            finally:
                out, err = self.capture_end()
            return process.returncode, out, err, total_time
