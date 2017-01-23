#
# Copyright (c) 2017 Intel Corporation
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

import subprocess
import sys

from .constants.logger_type import LoggerType
from .exceptions import CommandExecutionException
from .tap_logger import get_logger

LOG_SEPARATOR = " [...] "
MAX_CHARACTER_COUNT = 50000 - len(LOG_SEPARATOR)

logger = get_logger(LoggerType.SHELL_COMMAND)


def run(command: list, cwd: str=None) -> str:
    """Run specified command in subprocess and log real time output"""
    logger.info("Executing command: '{}'".format(" ".join(command)))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                               cwd=cwd)
    out = []
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output != '':
            logger.info(output.strip())
            out.append(output.strip())
            sys.stdout.flush()

    return_code = process.poll()

    if return_code != 0:
        exception_output = " ".join(out)
        if len(exception_output) > MAX_CHARACTER_COUNT:
            half = MAX_CHARACTER_COUNT // 2
            exception_output = "{}{}{}".format(exception_output[:half], LOG_SEPARATOR, exception_output[-half:])
        raise CommandExecutionException(return_code, exception_output, " ".join(command))

    return out


def run_interactive(command: list, prompt_answers: list, cwd=None) -> str:
    """Run specified command in subprocess and passes response to interactive prompt

    Args:
        command: terminal command split to list.
        prompt_answers: list of interactive answers to terminal prompt.
        cwd: currently working directory

    Returns:
        out: Command's stdout + stderr
    """
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.STDOUT, universal_newlines=True, cwd=cwd)

    out = []
    for ans in prompt_answers:
        output = process.communicate(ans+"\n")[0].rstrip()
        if output != '':
            logger.info(output.strip())
            out.append(output.strip())
            sys.stdout.flush()

    return_code = process.poll()

    if return_code in [0, 255]:
        return out

    exception_output = " ".join(out)
    if len(exception_output) > MAX_CHARACTER_COUNT:
        half = MAX_CHARACTER_COUNT // 2
        exception_output = "{}{}{}".format(exception_output[:half], LOG_SEPARATOR, exception_output[-half:])
    raise CommandExecutionException(return_code, exception_output, " ".join(command))
