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
import shutil
import socket
import subprocess
from distutils.version import StrictVersion

import pytest
from retry import retry

import config
import modules.command
from modules import file_utils
from modules.app_sources import AppSources
from modules.constants import TapGitHub, RelativeRepositoryPaths
from modules.constants.urls import Urls
from modules.tap_cli import TapCli
from modules.tap_logger import log_fixture, step


@pytest.fixture(scope="session")
def centos_key_path(request):
    path = config.ng_jump_key_path
    if path is None:
        ilab_deploy = AppSources.get_repository(repo_name=TapGitHub.ilab_deploy, repo_owner=TapGitHub.intel_data)
        path = os.path.join(ilab_deploy.path, RelativeRepositoryPaths.ilab_centos_key)
        request.addfinalizer(lambda: shutil.rmtree(ilab_deploy.path))
    subprocess.check_call(["chmod", "600", path])
    return path


@retry(ConnectionRefusedError, tries=20, delay=5)
def _check_tunnel_established(host, port):
    sock = socket.create_connection((host, port))
    sock.close()


@retry(subprocess.TimeoutExpired, tries=5, delay=2)
def _check_if_proc_finished(proc, command):
    if (None == proc.poll()):
        raise subprocess.TimeoutExpired(command, "")


def _get_latest_instance(centos_key_path):
    rex = re.compile(r'TAP-[0-9]+[\.][0-9]+[\.][0-9]+$')
    command = ["ssh", "-i", centos_key_path,
               "-o StrictHostKeyChecking=no",
               "{}@{}".format(config.ng_jump_username, config.ng_jump_ip),
               "ls"]
    result = modules.command.run(command)
    files = [s for s in result if rex.match(s)]
    assert len(files) > 0
    return str(max([StrictVersion(i.split('-')[1]) for i in files]))


@pytest.fixture(scope="session")
def open_tunnel(request, centos_key_path):
    assert config.ng_jump_ip is not None
    command = ["ssh", "{}@{}".format(config.ng_jump_username, config.ng_jump_ip),
               "-N",
               "-o StrictHostKeyChecking=no",
               "-i", centos_key_path,
               "-D", str(config.ng_socks_proxy_port)]
    log_fixture("Opening tunnel {}".format(" ".join(command)))
    tunnel = subprocess.Popen(command)
    try:
        log_fixture("Wait until tunnel is established")
        _check_tunnel_established("localhost", config.ng_socks_proxy_port)
    except:
        tunnel.kill()
        raise
    request.addfinalizer(tunnel.kill)


@pytest.fixture(scope="session")
def tap_cli(centos_key_path):
    assert config.ng_jump_username is not None
    assert config.ng_jump_ip is not None

    target_directory = "/tmp/"

    ng_build_number = config.ng_build_number
    if ng_build_number is None:
        ng_build_number = _get_latest_instance(centos_key_path)

    tap_binary = "TAP-" + ng_build_number + "/tap"

    log_fixture("Download tap client")
    command = ["scp", "-i", centos_key_path,
               "-o StrictHostKeyChecking=no",
               "{}@{}:{}".format(config.ng_jump_username, config.ng_jump_ip, tap_binary),
               target_directory]

    proc = subprocess.Popen(command)
    try:
        log_fixture("Waiting for tap client to download")
        _check_if_proc_finished(proc, command)
    except subprocess.TimeoutExpired:
        log_fixture("Command timeout: " + " ".join(command))
        proc.kill()
        raise

    command = ['chmod', '+x', '{}{}'.format(target_directory, 'tap')]
    modules.command.run(command)

    return TapCli("/tmp/")


@pytest.fixture(scope="session")
def cli_login(tap_cli):
    log_fixture("Login to TAP CLI")
    tap_cli.login()


@pytest.fixture(scope="function")
def sample_app_manifest_path(request):
    log_fixture("Download and return path to manifest.json")
    request.cls.manifest_file_path = file_utils.download_file(Urls.manifest_url, "manifest.json")
    return request.cls.manifest_file_path


@pytest.fixture(scope="class")
def sample_app_path(request):
    log_fixture("Download and return path to sample app")
    sample_app_url = getattr(request.cls, "SAMPLE_APP_URL")
    sample_app_tar_name = getattr(request.cls, "SAMPLE_APP_TAR_NAME")
    request.cls.application_file_path = file_utils.download_file(sample_app_url, sample_app_tar_name)
    return request.cls.application_file_path


@pytest.fixture(scope="class")
def remove_tmp_file_dir():
    log_fixture("Remove '{}' directory if exists".format(file_utils.TMP_FILE_DIR))
    if os.path.exists(file_utils.TMP_FILE_DIR):
        shutil.rmtree(file_utils.TMP_FILE_DIR)


@pytest.fixture(scope="class")
def download_unpack_and_check_sample_app(request, remove_tmp_file_dir, sample_app_path):
    log_fixture("Unpack and check content of sample app")
    sample_app_tar_name = getattr(request.cls, "SAMPLE_APP_TAR_NAME")
    step("Extract application archive")
    modules.command.run(["tar", "zxvf", sample_app_tar_name], cwd=file_utils.TMP_FILE_DIR)
    step("Remove archive file")
    modules.command.run(["rm", sample_app_tar_name], cwd=file_utils.TMP_FILE_DIR)
    step("Check application content")
    ls = modules.command.run(["ls"], cwd=file_utils.TMP_FILE_DIR)
    files_list = getattr(request.cls, "FILES_LIST")
    global app_file
    assert all(app_file in ls for app_file in files_list), "{} is missing".format(
        app_file)
