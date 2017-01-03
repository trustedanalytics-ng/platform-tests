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
import stat
import tarfile
from distutils.version import LooseVersion

import pytest

import config
from modules import file_utils
from modules.ssh_lib import JumpClient, JumpTunnel
from modules.tap_cli import TapCli
from modules.tap_logger import log_fixture
from modules.tap_object_model import ServiceOffering


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
def tap_cli():
    jump_client = JumpClient(username=config.ng_jump_user)

    tap_build_number = config.tap_build_number
    if tap_build_number is None:
        tap_build_number = _get_latest_tap_cli_instance(jump_client)

    tap_binary_name = "tap"
    remote_tap_binary_path = os.path.join("TAP-{}".format(tap_build_number), tap_binary_name)
    target_directory = os.path.join("/tmp")
    target_path = os.path.join(target_directory, tap_binary_name)

    if config.check_tap_cli_version and os.path.isfile(target_path):
        log_fixture("Deleting old tap client")
        os.remove(target_path)

    log_fixture("Download tap client")
    return_code = jump_client.scp_from_remote(source_path=remote_tap_binary_path, target_path=target_directory)
    if config.check_tap_cli_version and return_code != 0:
        pytest.fail("Latest tap client cannot be properly copied from jumpbox")
    os.chmod(target_path, os.stat(target_path).st_mode | stat.S_IEXEC)

    return TapCli(target_path)


@pytest.fixture(scope="session")
def cli_login(tap_cli):
    log_fixture("Login to TAP CLI")
    tap_cli.login()


@pytest.fixture(scope="class")
def sample_app_path(request):
    # NOTE: test class needs to have application source url specified as SAMPLE_APP_URL class variable
    sample_app_url = getattr(request.cls, "SAMPLE_APP_URL")
    sample_app_tar_name = sample_app_url.split("/")[-1]
    log_fixture("Download sample app: {}".format(sample_app_url))
    sample_app_path = file_utils.download_file(sample_app_url, sample_app_tar_name)
    request.addfinalizer(lambda: file_utils.remove_if_exists(sample_app_path))
    return sample_app_path


@pytest.fixture(scope="class")
def app_jar(request, sample_app_path):
    # NOTE: test class needs to have application type specified as APP_TYPE class variable
    app_type = getattr(request.cls, "APP_TYPE")
    sample_app_source_dir = os.path.join(os.path.dirname(sample_app_path),
                                         "sample_{}_app_source".format(app_type))
    with tarfile.open(sample_app_path) as tar:
        tar.extractall(path=sample_app_source_dir)
        sample_app_tar_content = [name.replace("./", "", 1) for name in tar.getnames()]
    return os.path.join(sample_app_source_dir, next(name for name in sample_app_tar_content if ".jar" in name))
