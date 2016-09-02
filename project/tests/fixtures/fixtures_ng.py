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
import shutil
import socket
import subprocess
import re
import modules.command
from distutils.version import StrictVersion

import pytest
from retry import retry

import config
from modules.app_sources import AppSources
from modules.constants import TapGitHub, RelativeRepositoryPaths
from modules.tap_cli import TapCli
from modules.tap_logger import log_fixture


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
    result = modules.command.run(command, return_output=True)
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
    modules.command.run(command, return_output=True)

    return TapCli("/tmp/")
