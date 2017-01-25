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

from datetime import datetime
import json
import logging
import os
import sys
import traceback

import requests
from teamcity import is_running_under_teamcity

import config
from .constants import LoggerType

__LOGGING_LEVEL = config.logging_level


class StdAndFileHandler(object):
    def __init__(self, stream, file_handler):
        self.stream = stream
        self.file_handler = file_handler

    def write(self, msg):
        self.stream.write(msg)
        self.file_handler.stream.write(msg)

    def flush(self):
        self.stream.flush()
        self.file_handler.stream.flush()


requests.packages.urllib3.disable_warnings()
logger_format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
if is_running_under_teamcity():
    logging.basicConfig(stream=sys.stdout, format=logger_format)
else:
    log_file_name = "api_tests_{}.log".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    default_log_dir = os.path.join("/tmp", log_file_name)
    fh = logging.FileHandler(default_log_dir)
    sh = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format=logger_format, handlers=[sh, fh])

    std_and_file_handler = StdAndFileHandler(sys.stdout, fh)
    def excepthook(etype, value, tb):
        s = "".join(traceback.format_exception(etype, value, tb))
        std_and_file_handler.write(s)
    sys.excepthook = excepthook


def change_log_file_path(log_file_dir):
    logger = logging.getLogger()
    log_dir = os.path.join(log_file_dir, log_file_name)
    if fh in logger.handlers:
        fh.close()  # close opened log file
        logger.removeHandler(fh)
        try:
            os.rename(default_log_dir, log_dir)  # try to move created log file to new directory
        except OSError:
            logger.exception("Can't move log file '{}' to '{}'.".format(default_log_dir, log_dir))
    new_file_handler = logging.FileHandler(log_dir)
    new_file_handler.setFormatter(logging.Formatter(logger_format))
    std_and_file_handler.file_handler = new_file_handler
    logger.addHandler(new_file_handler)


def set_level(level_name):
    global __LOGGING_LEVEL
    __LOGGING_LEVEL = getattr(logging, level_name)
    # set logging level to all already-defined loggers
    for _, logger in logging.Logger.manager.loggerDict.items():
        if not isinstance(logger, logging.PlaceHolder):
            logger.setLevel(__LOGGING_LEVEL)
    # set custom logging levels to third-party library loggers
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(__LOGGING_LEVEL)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(__LOGGING_LEVEL)
    return logger


def log_command(command, replace=None):
    logger = get_logger(LoggerType.SHELL_COMMAND)
    msg = "Execute {}".format(" ".join(command))
    if replace is not None:
        msg = msg.replace(*replace)
    logger.info(msg)


def log_http_request(prepared_request, username, password=None, description="", data=None):
    prepared_body = prepared_request.body[:5000] if prepared_request.body else prepared_request.body
    body = prepared_body if not data else json.dumps(data)
    if body is None:
        body = ""
    msg = [
        description,
        "----------------Request------------------",
        "Client name: {}".format(username),
        "URL: {} {}".format(prepared_request.method, prepared_request.url),
        "Headers: {}".format(prepared_request.headers),
        "Body: {}".format(body),
        "-----------------------------------------"
    ]
    get_logger(LoggerType.HTTP_REQUEST).debug("\n".join(msg))


def log_http_response(response, logged_body_length=None):
    """If logged_body_length < 0, full response body is logged"""
    if logged_body_length is None:
        logged_body_length = int(config.logged_response_body_length)
    body = None
    if logged_body_length == 0:
        body = "[...]"
    elif len(response.text) > logged_body_length > 0:
        half = logged_body_length // 2
        body = "{} [...] {}".format(response.text[:half], response.text[-half:])
    msg = [
        "\n----------------Response------------------",
        "Status code: {}".format(response.status_code),
        "Headers: {}".format(response.headers),
        "Content: {}".format(body if body is not None else response.text),
        "-----------------------------------------\n"
    ]
    get_logger(LoggerType.HTTP_RESPONSE).debug("\n".join(msg))


def step(message):
    separator = "=" * 20
    _log_separator(logger_type=LoggerType.STEP_LOGGER, separator=separator, message=message)


def log_fixture(message):
    separator = "*" * 20
    _log_separator(logger_type=LoggerType.FIXTURE_LOGGER, separator=separator, message=message)


def log_finalizer(message):
    separator = "*" * 20
    _log_separator(logger_type=LoggerType.FINALIZER_LOGGER, separator=separator, message=message)


def _log_separator(logger_type, separator, message):
    get_logger(logger_type).info("{0} {1} {0}".format(separator, message))
