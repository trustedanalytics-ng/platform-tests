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

import yaml

from .constants import TapComponent, TapGitHub
from .app_sources import github_get_file_content
import config


class VersionedComponent(object):
    def __init__(self, component: TapComponent, version: str):
        self.__component = component
        self.__version = version

    @property
    def to_db_format(self):
        return {"name": self.__component.name, "version": self.__version}

    @staticmethod
    def list_to_db_format(component_list):
        return [c.to_db_format for c in component_list]


def get_appstack_yml(github_org_name=None):
    """
    Read local appstack file if a path is configured, otherwise download the file from github.
    """
    if config.appstack_file_path is not None:
        with open(config.appstack_file_path) as f:
            appstack_file = f.read()
    else:
        appstack_file = github_get_file_content(repository=TapGitHub.apployer, file_path=TapGitHub.appstack_path,
                                                owner=github_org_name, ref=config.appstack_version,
                                                github_auth=config.github_credentials())
    return yaml.load(appstack_file)
