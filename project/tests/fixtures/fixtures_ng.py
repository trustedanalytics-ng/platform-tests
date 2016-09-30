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
from distutils.version import StrictVersion

import pytest

import config
from modules import file_utils
from modules.constants.urls import Urls
from modules.ssh_lib import JumpClient, JumpTunnel
from modules.tap_cli import TapCli
from modules.tap_logger import log_fixture


@pytest.fixture(scope="session")
def open_tunnel(request):
    jump_tunnel = JumpTunnel()
    jump_tunnel.open()
    request.addfinalizer(jump_tunnel.close)
    return jump_tunnel


def _get_latest_tap_cli_instance(jumpbox_client):
    result = jumpbox_client.ssh("ls")
    rex = re.compile(r'TAP-[0-9]+[\.][0-9]+[\.][0-9]+$')
    files = [s for s in result if rex.match(s)]
    assert len(files) > 0
    return str(max([StrictVersion(i.split('-')[1]) for i in files]))


@pytest.fixture(scope="session")
def tap_cli():
    jump_client = JumpClient(username=config.ng_jump_user)

    ng_build_number = config.ng_build_number
    if ng_build_number is None:
        ng_build_number = _get_latest_tap_cli_instance(jump_client)

    tap_binary_name = "tap"
    remote_tap_binary_path = os.path.join("TAP-{}".format(ng_build_number), tap_binary_name)
    target_directory = os.path.join("/tmp")
    target_path = os.path.join(target_directory, tap_binary_name)

    log_fixture("Download tap client")
    jump_client.scp_from_remote(source_path=remote_tap_binary_path, target_path=target_directory)
    os.chmod(target_path, os.stat(target_path).st_mode | stat.S_IEXEC)

    return TapCli(target_path)


@pytest.fixture(scope="session")
def cli_login(tap_cli):
    log_fixture("Login to TAP CLI")
    tap_cli.login()


@pytest.fixture(scope="class")
def sample_manifest_path(request):
    log_fixture("Download sample manifest.json")
    sample_manifest_path = file_utils.download_file(Urls.manifest_url, "manifest.json")
    request.addfinalizer(lambda: file_utils.remove_if_exists(sample_manifest_path))
    return sample_manifest_path


@pytest.fixture(scope="class")
def sample_app_path(request):
    # NOTE: test class needs to have application source url specified as SAMPLE_APP_URL class variable
    sample_app_url = getattr(request.cls, "SAMPLE_APP_URL")
    sample_app_tar_name = sample_app_url.split("/")[-1]
    log_fixture("Download sample app: {}".format(sample_app_url))
    sample_app_path = file_utils.download_file(sample_app_url, sample_app_tar_name)
    request.addfinalizer(lambda: file_utils.remove_if_exists(sample_app_path))
    return sample_app_path
