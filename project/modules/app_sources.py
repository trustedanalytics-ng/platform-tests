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

import base64
import json
import os
import subprocess

from git import Repo
import requests

from .tap_logger import log_command, get_logger, log_http_request, log_http_response


logger = get_logger(__name__)


class AppSources(object):

    def __init__(self, sources_directory):
        self.path = sources_directory

    @staticmethod
    def __get_repo_url(repo_name, repo_owner, gh_auth=None) -> str:
        if gh_auth is not None:
            clone_url = "https://{}:{}@github.com/{}/{}.git".format(gh_auth[0], gh_auth[1], repo_owner, repo_name)
        else:
            clone_url = "https://github.com/{}/{}.git".format(repo_owner, repo_name)
        return clone_url

    @classmethod
    def from_local_path(cls, sources_directory):
        return cls(sources_directory=sources_directory)

    @classmethod
    def from_github(cls, repo_name, repo_owner, target_directory=None, gh_auth=None):
        if target_directory is None:
            target_directory = os.path.join("/tmp", repo_owner, repo_name)
        cls._clone_or_pull(repo_name, repo_owner, target_directory, gh_auth)
        return cls(sources_directory=target_directory)

    @classmethod
    def _clone_or_pull(cls, repo_name, repo_owner, target_directory, gh_auth=None) -> str:
        """Pull changes into repository if repository exists, otherwise clone it"""
        repo_url = cls.__get_repo_url(repo_name, repo_owner, gh_auth)
        if os.path.exists(target_directory):
            logger.info("Pull from {}".format(repo_url))
            repo = Repo(target_directory)
            repo.head.reset("--hard")
            origin = repo.remotes.origin
            origin.pull()
        else:
            logger.info("Clone from {} to {}".format(repo_url, target_directory))
            os.makedirs(target_directory, exist_ok=True)
            Repo.clone_from(repo_url, target_directory)

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

