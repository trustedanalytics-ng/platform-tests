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
from multiprocessing import Queue

from ..tap_logger import get_logger
from ..constants.logger_type import LoggerType
from project.modules.remote_logger.config import Config
from .log_provider import LogProvider
from .log_provider_configuration import LogProviderConfiguration
from .remote_logger_configuration import RemoteLoggerConfiguration
from project.modules.ssh_lib import JumpTunnel

logger = get_logger(LoggerType.REMOTE_LOGGER)


class RemoteLogger(object):
    """Object for getting logs from remote sources."""

    def __init__(self, configuration: RemoteLoggerConfiguration):
        self.__configuration = configuration

    def run_logging_procedure(self):
        """Block which connects methods."""
        try:
            logs = self.__get_logs()
            self.__save_logs(logs)
        except Exception as e:
            logger.error(e)

    def log_to_file(self):
        """Read remote logs and write them to file."""
        if Config.TUNNEL_AVAILABLE:
            self.run_logging_procedure()
        else:
            logger.info("Ssh tunnel not available, creating tunnel for remote logger.")
            jump_tunnel = JumpTunnel()
            jump_tunnel.open()
            try:
                self.run_logging_procedure()
            finally:
                jump_tunnel.close()

    def __get_logs(self):
        """Run multiple log providers, one for each application.
        Wait for each process to finish and then collect all logs that have been read."""
        queue = Queue()
        processes = []
        logs = {}
        logger.info("Start collecting remote logs")
        for app_name in self.__configuration.app_names:
            log_provider_configuration = self.__create_log_provider_configuration(app_name)
            process = LogProvider(log_provider_configuration, queue)
            processes.append(process)
            process.start()
        for i in range(len(self.__configuration.app_names)):
            logs.update(queue.get())
        for p in processes:
            p.join()
        return logs

    def __create_log_provider_configuration(self, app_name):
        """Create log provider configuration."""
        return LogProviderConfiguration(
            from_date=self.__configuration.from_date,
            to_date=self.__configuration.to_date,
            app_name=app_name
        )

    def __save_logs(self, logs):
        """Write logs to files, one separate file for each application name."""
        dir_path = os.path.join(Config.ROOT_DIRECTORY, self.__configuration.destination_directory)
        os.makedirs(dir_path, exist_ok=True)
        for app_name, app_log in logs.items():
            if app_log != LogProvider.EMPTY_LOG:
                self.__save_log(app_name, app_log, dir_path)
            else:
                logger.error("Empty log has been returned for: {}".format(app_name))

    @staticmethod
    def __save_log(app_name, app_log, dir_path):
        """Write log to file."""
        file_name = Config.LOG_FILE_NAME.format(app_name)
        file_path = os.path.join(dir_path, file_name)
        logger.info("Save log to file: {}".format(file_path))
        with open(file_path, 'w') as file:
            file.write(app_log)
