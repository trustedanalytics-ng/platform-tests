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

import pytest
from retry import retry

import config
from modules.app_sources import AppSources
from modules.constants import TapGitHub, RelativeRepositoryPaths
from modules.tap_logger import log_fixture


@pytest.fixture(scope="session")
def centos_key_path(request):
    path = config.ng_jump_key_path
    if path is None:
        ilab_deploy = AppSources.from_github(repo_name=TapGitHub.ilab_deploy, repo_owner=TapGitHub.intel_data,
                                             gh_auth=config.github_credentials())
        path = os.path.join(ilab_deploy.path, RelativeRepositoryPaths.ilab_centos_key)
        request.addfinalizer(lambda: shutil.rmtree(ilab_deploy.path))
    subprocess.check_call(["chmod", "600", path])
    return path


@retry(ConnectionRefusedError, tries=20, delay=5)
def _check_tunnel_established(host, port):
    sock = socket.create_connection((host, port))
    sock.close()


@pytest.fixture(scope="session")
def open_tunnel(request, centos_key_path):
    assert config.ng_jump_ip is not None
    command = ["ssh", "{}@{}".format(config.ng_jump_username, config.ng_jump_ip),
               "-N",
               "-oStrictHostKeyChecking=no",
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
