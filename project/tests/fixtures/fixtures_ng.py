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
from modules.constants import TapGitHub, RelativeRepositoryPaths, ApplicationPath
from modules.constants.urls import Urls
from modules.tap_cli import TapCli
from modules.tap_logger import log_fixture, step
from modules.tap_object_model import Application


@pytest.fixture(scope="session")
def centos_key_path(request):
    path = config.ng_jump_key_path
    if path is None:
        ilab_deploy = AppSources.get_repository(repo_name=TapGitHub.ilab_deploy, repo_owner=TapGitHub.intel_data)
        path = os.path.join(ilab_deploy.path, RelativeRepositoryPaths.ilab_centos_key)
        request.addfinalizer(lambda: shutil.rmtree(ilab_deploy.path))
        # TODO: Use library calls instead of subprocess
        subprocess.check_call(["chmod", "600", path])
    path = os.path.expanduser(path)
    assert os.path.isfile(path), "No such file {}".format(path)
    return path


@retry(ConnectionRefusedError, tries=10, delay=5)
def _check_tunnel_established(host, port):
    sock = socket.create_connection((host, port))
    sock.close()


@retry(subprocess.TimeoutExpired, tries=5, delay=30)
def _check_if_proc_finished(proc, command):
    if (None == proc.poll()):
        raise subprocess.TimeoutExpired(command, "")


def _get_latest_instance(centos_key_path):
    rex = re.compile(r'TAP-[0-9]+[\.][0-9]+[\.][0-9]+$')
    command = ["ssh", "-i", centos_key_path,
               "-o UserKnownHostsFile=/dev/null",
               "-o StrictHostKeyChecking=no", "-o GSSAPIAuthentication=no",
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
               "-o UserKnownHostsFile=/dev/null",
               "-o StrictHostKeyChecking=no", "-o GSSAPIAuthentication=no",
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
               "-o UserKnownHostsFile=/dev/null",
               "-o StrictHostKeyChecking=no", "-o GSSAPIAuthentication=no",
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


@pytest.fixture(scope="class")
def download_unpack_and_check_sample_app(request, sample_app_path):
    log_fixture("Unpack and check content of sample app")
    step("Extract application archive")
    modules.command.run(["tar", "zxvf", sample_app_path], cwd=file_utils.TMP_FILE_DIR)
    step("Remove archive file")
    modules.command.run(["rm", sample_app_path], cwd=file_utils.TMP_FILE_DIR)
    step("Check application content")
    ls = modules.command.run(["ls"], cwd=file_utils.TMP_FILE_DIR)
    file_list = getattr(request.cls, "FILES_LIST")
    missing_files = [app_file for app_file in file_list if app_file not in ls]
    assert len(missing_files) == 0, "Missing files: {}".format(", ".join(missing_files))

