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
import re

import pexpect

import config
from .. import command as cmd
from ..exceptions import AtkScriptException
from ..hive import Hive
from ..tap_logger import log_command, get_logger


logger = get_logger(__name__)


class PexpectLoggerAdapter(object):

    def __init__(self, logger_name, obscured_secret=None):
        self.logger = get_logger(logger_name)
        self.obscured_secret = obscured_secret

    def write(self, data):
        data = data.decode("utf-8").strip()
        if data:  # non-blank
            if self.obscured_secret is not None:
                data = data.replace(self.obscured_secret, "[SECRET]")
            self.logger.info(data)

    def flush(self):
        pass  # leave it to logging to flush properly


class ATKtools(object):

    TEST_SCRIPTS_DIRECTORY = os.path.join("fixtures", "atk_test_scripts")
    HIVE_CLEANUP_SCRIPT = os.path.join(TEST_SCRIPTS_DIRECTORY, "remove_test_tables.py")
    CREDENTIALS_FILE_PATH = "/tmp/atk_credentials_file"

    def __init__(self, name, interpreter_version="python2"):
        self.path = os.path.join("/tmp", name)
        self.system_interpreter = os.path.join("/usr/bin", interpreter_version)
        self.interpreter = os.path.join(self.path, "bin", interpreter_version)
        self.pip = os.path.join(self.path, "bin/pip")
        self.installed_packages = []

    @staticmethod
    def dataset_uri_to_atk_uri(dataset_uri):
        pattern = r"userspace.*$"
        match = re.search(pattern, dataset_uri)
        if match is None:
            raise AssertionError("Pattern not found in dataset uri")
        return "../../../{}".format(match.group())

    @staticmethod
    def get_atk_client_url(atk_url):
        return "http://{}/client".format(atk_url)

    @staticmethod
    def get_expected_atk_app_name(atk_service_instance):
        return "{}-{}".format(atk_service_instance.name, atk_service_instance.guid.split("-")[0])

    def teardown(self, atk_url=None, org=None):
        # Cleanup hive
        if org is not None:
            hive = Hive()
            hive.exec_query("DROP DATABASE IF EXISTS {} CASCADE;".format(org.name))

        if atk_url is not None and self.get_atk_client_url(atk_url) in self.installed_packages:
            try:
                self.run_atk_script(self.HIVE_CLEANUP_SCRIPT, atk_url)
            except AtkScriptException as e:
                logger.warning("Could not cleanup hive: DPNG-4579\n{}".format(e))
            else:
                raise AssertionError("Unexpected success: Is DPNG-4579 fixed yet on this environment?")
        # Delete credentials file
        if os.path.exists(self.CREDENTIALS_FILE_PATH):
            os.remove(self.CREDENTIALS_FILE_PATH)
        # Delete virtualenv directory
        self.delete()

    def create(self):
        command = ["virtualenv", "-p", self.system_interpreter, self.path]
        log_command(command)
        cmd.run(command)

    def delete(self):
        command = ["rm", "-rf", self.path]
        log_command(command)
        cmd.run(command)

    def pip_install(self, package_name, **pip_options):
        self.installed_packages.append(package_name)
        command = [self.pip, "install"]
        for option_name, value in pip_options.items():
            command += ["--" + option_name.replace("_", "-"), value]
        command += [package_name]
        log_command(command)
        cmd.run(command)

    def run_atk_script(self, script_path, atk_url, positional_arguments=None, arguments=None, use_uaa=True,
                       timeout=480):
        command = [self.interpreter, script_path]
        if positional_arguments is not None:
            command += positional_arguments
        if arguments is not None:
            for k, v in arguments.items():
                command += [k, v]
        if use_uaa:
            command += ["--uaa_file_name", self.CREDENTIALS_FILE_PATH]
        log_command(command)

        username = config.admin_username
        password = config.admin_password

        child = pexpect.spawn(" ".join(command))
        child.logfile_read = PexpectLoggerAdapter(logger_name="atk-client-out", obscured_secret=password)
        child.logfile_send = PexpectLoggerAdapter(logger_name="atk-client-in", obscured_secret=password)
        child.expect("URI of the ATK server:")
        child.sendline(atk_url)
        child.expect("User name:")
        child.sendline(username)
        child.expect("Password:")
        child.sendline(password)

        child.sendline("y")
        child.expect(pexpect.EOF, timeout=timeout)
        response = child.before.decode("utf-8")

        if "Traceback" in response:
            raise AtkScriptException("Python exception in atk client")
        if "Connected" not in response:
            raise AtkScriptException("Python client failed to connect to ATK instance")
        
        return response
