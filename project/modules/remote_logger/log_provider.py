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

from multiprocessing import Process, Queue
from os import getpid
from time import sleep

from ..tap_logger import get_logger
from ..constants.logger_type import LoggerType
from .config import Config
from .elastic_search import ElasticSearch
from .log_provider_configuration import LogProviderConfiguration

logger = get_logger(LoggerType.REMOTE_LOGGER)


class LogProvider(Process):
    """Object for getting logs form elastic search."""

    EMPTY_LOG = ""
    TRIALS_LOG = "PID: {} - APP: {} - Try number: {}"
    EXCEPTION_LOG = "PID: {} - APP: {} - Exception: {}"

    def __init__(self, configuration: LogProviderConfiguration, queue: Queue):
        super().__init__()
        self.__configuration = configuration
        self.__queue = queue
        self.__log = None

    def run(self):
        """Worker function to get logs from elastic search."""
        sleep(Config.TIME_BEFORE_NEXT_CALL)
        try:
            elastic_search = ElasticSearch(self.__configuration)
            trials_number = 0
            while not elastic_search.is_log_ready():
                trials_number += 1
                if trials_number > Config.REMOTE_LOGGER_RETRY_COUNT:
                    raise LogProviderExceededTrialsNumberException()
                logger.info(self.TRIALS_LOG.format(getpid(), self.__configuration.app_name, trials_number))
                sleep(Config.TIME_BEFORE_NEXT_CALL)
            self.__log = elastic_search.get_log()
        except Exception as e:
            logger.error(self.EXCEPTION_LOG.format(getpid(), self.__configuration.app_name, e))
            self.__log = self.EMPTY_LOG
        else:
            logger.info("Logs collected and converted successfully")
        finally:
            self.__update_queue()

    def __update_queue(self):
        """Put log results dictionary into process queue."""
        self.__queue.put({self.__configuration.app_name: self.__log})


class LogProviderExceededTrialsNumberException(Exception):
    def __init__(self):
        super().__init__("Number of trials has been exceeded.")
