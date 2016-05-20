#
# Copyright (c) 2015-2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import base64
import json
import os
import subprocess

from git import Repo
import requests

from configuration import config
from .tap_logger import log_command, get_logger, log_http_request, log_http_response


logger = get_logger(__name__)


class AppSources(object):

    def __init__(self, repo_name: str, repo_owner: str, target_directory: str=None, gh_auth: tuple=None):
        self.repo_name = repo_name
        self.repo_owner = repo_owner
        if target_directory is None:
            target_directory = os.path.join("/tmp", repo_owner, repo_name)
        self.path = target_directory
        self.gh_auth = gh_auth

    def __get_repo_url(self) -> str:
        if self.gh_auth is not None:
            clone_url = "https://{}:{}@github.com/{}/{}.git".format(self.gh_auth[0], self.gh_auth[1],
                                                                    self.repo_owner, self.repo_name)
        else:
            clone_url = "https://github.com/{}/{}.git".format(self.repo_owner, self.repo_name)
        return clone_url

    def __clone(self):
        repo_url = self.__get_repo_url()
        logger.info("Clone from {} to {}".format(repo_url, self.path))
        os.makedirs(self.path, exist_ok=True)
        Repo.clone_from(repo_url, self.path)

    def clone_or_pull(self) -> str:
        """Pull changes into repository if repository exists, otherwise clone it"""
        if os.path.exists(self.path):
            repo_url = self.__get_repo_url()
            logger.info("Pull from {}".format(repo_url))
            repo = Repo(self.path)
            repo.head.reset("--hard")
            origin = repo.remotes.origin
            origin.pull()
        else:
            self.__clone()
        return self.path

    def compile_mvn(self, working_directory: str=None):
        logger.info("Compile with maven")
        self.__compile(["mvn", "clean", "package"], working_directory=working_directory)

    def compile_gradle(self, working_directory: str=None):
        logger.info("Compile with gradle")
        self.__compile(["./gradlew", "assemble"], working_directory=working_directory)

    def __compile(self, command: list, working_directory: str=None):
        if working_directory is None:
            working_directory = self.path
        current_path = os.getcwd()
        os.chdir(working_directory)
        log_command(command)
        subprocess.call(command)
        os.chdir(current_path)

    def checkout_commit(self, commit_id: str):
        """
        Create a branch which points to commit_id and switch to it or checkout and reset if the branch exists
        """
        branch_name = "branch_{}".format(commit_id)
        repo = Repo(self.path)
        if branch_name not in repo.branches:
            logger.info("Create branch {}".format(branch_name))
            repo.git.checkout(commit_id, b=branch_name)
        else:
            logger.info("Switch to branch {}".format(branch_name))
            repo.git.checkout(commit_id, B=branch_name)


def github_get_file_content(repository, file_path, owner, ref=None, github_auth=None):
    url = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repository, file_path)
    session = requests.session()
    request = session.prepare_request(requests.Request(method="GET", url=url, params={"ref": ref}, auth=github_auth))
    log_http_request(request, "")
    response = session.send(request)
    log_http_response(response)
    if response.status_code != 200:
        raise Exception("Github API response is {} {}".format(response.status_code, response.text))
    encoding = response.encoding
    response_content = response.content.decode(encoding)
    return base64.b64decode(json.loads(response_content)["content"])

