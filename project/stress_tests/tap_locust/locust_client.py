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
import subprocess
import sys
import time

import signal

from locust import events, Locust
import pytest
import _pytest.main as pytest_main

from ._stream_capture import StreamCapture

project_path = os.path.abspath(os.path.join(__file__, "..", "..", ".."))

logger = logging.getLogger(__name__)


class LocustClient(object):
    CAPTURE_PYTEST_OUTPUT = False

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

    def run(self, locust_instance: Locust, test_module_path: str, test_class_name: str=None, test_name: str=None,
            pytest_params: list=None):
        pytest_params = pytest_params or []
        pytest_selector = [s for s in (test_module_path, test_class_name, test_name) if s is not None]
        pytest_selector = "::".join(pytest_selector)

        logger.info("Starting pytest with {}".format(str([pytest_selector]+pytest_params)))
        ret_code, out, err, exec_time = self.run_pytest(pytest_selector, pytest_params)
        logger.info("Pytest exit with code: {}".format(ret_code))

        if ret_code == pytest_main.EXIT_OK:
            events.request_success.fire(request_type="test", name=pytest_selector, response_time=exec_time,
                                        response_length=0)
        elif ret_code == pytest_main.EXIT_TESTSFAILED:
            events.request_failure.fire(request_type="test", name=pytest_selector, response_time=exec_time,
                                        exception=out+err)
        else:
            events.locust_error(locust_instance, exception=None, tb=out+err)

    def run_pytest(self, selector, params):
        process = None
        command = ["py.test", selector] + params
        self.capture_start()
        try:
            start_time = time.time()
            process = subprocess.Popen(command, cwd=project_path, universal_newlines=True)
            process.wait()
            total_time = int((time.time() - start_time) * 1000)
        except:
            logger.warn("Terminating pytest")
            process.send_signal(signal.SIGINT)
            raise
        finally:
            out, err = self.capture_end()
        return process.returncode, out, err, total_time
