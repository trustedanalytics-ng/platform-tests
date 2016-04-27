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

import ctypes
import logging
import multiprocessing
import os
import signal
import subprocess
import sys
import time

from config import RunnerConfig, DatabaseConfig
from model import TestSuiteModel

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Runner(object):
    _instance = None
    _config = RunnerConfig()
    _db_config = DatabaseConfig()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._is_busy = multiprocessing.Value(ctypes.c_bool, False)
        self._pid = multiprocessing.Value(ctypes.c_int, -1)
        self._test_cwd = self._config.cwd
        self._current_suite = None
        self._username = None
        self._password = None
        self._start_time = 0

    @property
    def is_busy(self):
        self._ensure_max_execution_time_not_exceeded()
        return self._is_busy.value

    @property
    def command(self):
        return [
            self._config.python_interpreter,
            self._config.run_tests,
            "-e", self._config.tap_domain,
            "-s", self._config.suite_name,
            "--admin-username", self._username,
            "--admin-password", self._password,
            "--reference-org", self._config.core_org_name,
            "--reference-space", self._config.core_space_name,
            "--database-url", self._db_config.uri,
            "--test-run-id", str(self._current_suite.id)
        ]

    def run(self, username, password):
        """
        Get new suite id, set current_suite_id. Start tests in a separate process.
        Return suite id.
        """
        self._username = username
        self._password = password
        self._current_suite = TestSuiteModel.initialize()
        self._is_busy.value = True
        self._start_time = time.time()
        multiprocessing.Process(target=self._worker).start()
        return self._current_suite

    def _ensure_max_execution_time_not_exceeded(self):
        if self._is_busy.value and time.time() - self._start_time > self._config.max_execution_time:
            logger.warning("Killing subprocess {}".format(self._pid.value))
            os.kill(self._pid.value, signal.SIGKILL)
            self._is_busy.value = False

    def _worker(self):
        """
        Run tests in a subprocess.
        If the subprocess' exit code is not 0, or the process failed to start,
        set suite status to interrupted.
        Mark that the runner is not busy.
        """
        try:
            logger.info("Running command {}".format(" ".join(self.command)))
            process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       universal_newlines=True, cwd=self._test_cwd)
            self._pid.value = process.pid
            while True:
                output = process.stdout.readline().strip()
                if output == "" and process.poll() is not None:
                    break
                if output != "":
                    logger.info(output)
                    sys.stdout.flush()

            return_code = process.poll()
            if return_code != 0:
                self._current_suite.set_interrupted()
                logger.error("Subprocess failed with exit code {}".format(return_code))
        except:
            self._current_suite.set_interrupted()
            logger.error(sys.exc_info()[0])
        finally:
            self._is_busy.value = False

