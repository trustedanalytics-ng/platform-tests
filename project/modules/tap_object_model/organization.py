#
# Copyright (c) 2015-2016 Intel Corporation
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

import functools

from retry import retry

from ..exceptions import UnexpectedResponseError
from ..http_calls import cloud_foundry as cf, platform as api
from ..tap_logger import get_logger
from ..test_names import get_test_name


logger = get_logger(__name__)


@functools.total_ordering
class Organization(object):

    TEST_ORG_NAMES = []

    def __init__(self, name, guid=None):
        self.name = name
        self.guid = guid
        self.metrics = {}

    def __repr__(self):
        return "{} (name={}, guid={})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def api_create(cls, name=None, client=None):
        name = get_test_name() if name is None else name
        cls.TEST_ORG_NAMES.append(name)
        response = api.api_create_organization(name, client=client)
        org = cls(name=name, guid=response)
        return org

    @classmethod
    def api_get_list(cls, client=None):
        response = api.api_get_organizations(client=client)
        organizations = []
        for organization_data in response:
            org = cls(name=organization_data["name"], guid=organization_data["guid"])
            organizations.append(org)
        return organizations

    def rename(self, new_name, client=None):
        self.name = new_name
        return api.api_rename_organization(self.guid, new_name, client=client)

    def api_delete(self, client=None):
        api.api_delete_organization(self.guid, client=client)

    def api_get_metrics(self, client=None):
        self.metrics = api.api_get_org_metrics(self.guid, client=client)

    @classmethod
    def cf_api_get_list(cls):
        response = cf.cf_api_get_orgs()
        org_list = []
        for org_info in response:
            org_list.append(cls(name=org_info["entity"]["name"], guid=org_info["metadata"]["guid"]))
        return org_list

    @retry(UnexpectedResponseError, tries=2, delay=5)
    def cf_api_delete(self):
        cf.cf_api_delete_org(self.guid)
