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

import os
import re
import stat
import tarfile
from distutils.version import LooseVersion

import pytest

import config
from modules.file_utils import TMP_FILE_DIR
from modules.ssh_lib import JumpClient, JumpTunnel
from modules.tap_cli import TapCli
from modules.tap_logger import log_fixture


TARGET_DIRECTORY = "/tmp"


@pytest.fixture(scope="session")
def open_tunnel(request):
    log_fixture("Open SSH tunnel to jumpbox")
    jump_tunnel = JumpTunnel()
    jump_tunnel.open()
    log_fixture("SSH tunnel to jumpbox is open")
    request.addfinalizer(jump_tunnel.close)
    return jump_tunnel


def _get_latest_tap_cli_instance(jumpbox_client):
    result = jumpbox_client.ssh("ls")
    rex = re.compile(r'TAP-[0-9]+[\.][0-9]+[\.][0-9]+(\.[0-9]+)?$')
    files = [s for s in result if rex.match(s)]
    assert len(files) > 0
    return str(max([LooseVersion(i.split('-')[1]) for i in files]))


@pytest.fixture(scope="session")
def jump_client():
    return JumpClient(username=config.ng_jump_user)


@pytest.fixture(scope="session")
def remote_tap_directory(jump_client):
    build_number = config.tap_build_number
    if build_number is None:
        build_number = _get_latest_tap_cli_instance(jump_client)
    return "TAP-{}".format(build_number)


@pytest.fixture(scope="session")
def jumpbox_model_file(remote_tap_directory, jump_client):
    model_name = "model.mar"
    remote_model_path = os.path.join(remote_tap_directory, "files/sample_apps/space-shuttle-demo", model_name)
    target_model_path = os.path.join(TARGET_DIRECTORY, model_name)
    return_code = jump_client.scp_from_remote(source_path=remote_model_path, target_path=TARGET_DIRECTORY)
    if config.check_tap_cli_version and return_code != 0:
        pytest.fail("Model file cannot be properly copied from jumpbox")
    return target_model_path


@pytest.fixture(scope="session")
def tap_cli(request, remote_tap_directory, jump_client):
    tap_binary_name = "tap"
    remote_tap_binary_path = os.path.join(remote_tap_directory, tap_binary_name)
    target_path = os.path.join(TARGET_DIRECTORY, tap_binary_name)

    if config.check_tap_cli_version and os.path.isfile(target_path):
        log_fixture("Deleting old tap client")
        os.remove(target_path)

    log_fixture("Download tap client")
    return_code = jump_client.scp_from_remote(source_path=remote_tap_binary_path, target_path=TARGET_DIRECTORY)
    if config.check_tap_cli_version and return_code != 0:
        pytest.fail("Latest tap client cannot be properly copied from jumpbox")
    os.chmod(target_path, os.stat(target_path).st_mode | stat.S_IEXEC)

    def fin():
        try:
            log_fixture("Deleting tap client")
            os.remove(target_path)
        except:
            pass
    request.addfinalizer(fin)

    return TapCli(target_path)


@pytest.fixture(scope="session")
def cli_login(tap_cli):
    log_fixture("Login to TAP CLI")
    tap_cli.login()


@pytest.fixture(scope="class")
def app_jar(test_sample_apps):
    sample_app_source_dir = os.path.join(TMP_FILE_DIR, "sample_java_app_source")
    with tarfile.open(test_sample_apps.tapng_java_app.filepath) as tar:
        tar.extractall(path=sample_app_source_dir)
        sample_app_tar_content = [name.replace("./", "", 1) for name in tar.getnames()]
    return os.path.join(sample_app_source_dir, next(name for name in sample_app_tar_content if name.endswith(".jar")))
