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

from configuration.config import CONFIG
from ..exceptions import UnexpectedResponseError
from ..http_calls import cloud_foundry as cf, platform as api
from ..tap_logger import get_logger
from ..test_names import get_test_name
from . import Space

logger = get_logger(__name__)


@functools.total_ordering
class Organization(object):

    TEST_ORGS = []

    def __init__(self, name, guid=None, spaces=None):
        self.name = name
        self.guid = guid
        self.spaces = [] if spaces is None else spaces
        self.metrics = {}

    def __repr__(self):
        return "{0} (name={1}, guid={2}, spaces={3})".format(self.__class__.__name__, self.name, self.guid, self.spaces)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def api_create(cls, name=None, client=None):
        name = get_test_name() if name is None else name
        response = api.api_create_organization(name, client=client)
        org = cls(name=name, guid=response)
        cls.TEST_ORGS.append(org)
        return org

    @classmethod
    def api_get_list(cls, client=None):
        response = api.api_get_organizations(client=client)
        organizations = []
        for organization_data in response:
            spaces = [Space(name=space_data["name"], guid=space_data["guid"])
                      for space_data in organization_data["spaces"]]
            org = cls(name=organization_data["name"], guid=organization_data["guid"], spaces=spaces)
            organizations.append(org)
        return organizations

    @classmethod
    def get_ref_org_and_space(cls):
        """Return org and space objects for reference org and space (e.g. seedorg, seedspace)"""
        ref_org_guid, ref_space_guid = cf.cf_get_ref_org_and_space_guids()
        org = Organization(name=CONFIG["ref_org_name"], guid=ref_org_guid)
        space = Space(name=CONFIG["ref_space_name"], guid=ref_space_guid)
        return org, space

    def rename(self, new_name, client=None):
        self.name = new_name
        return api.api_rename_organization(self.guid, new_name, client=client)

    def api_delete(self, client=None):
        if self in self.TEST_ORGS:
            self.TEST_ORGS.remove(self)
        api.api_delete_organization(self.guid, client=client)

    def api_get_metrics(self, client=None):
        self.metrics = api.api_get_org_metrics(self.guid, client=client)

    def api_get_spaces(self, client=None):
        response = api.api_get_spaces_in_org(org_guid=self.guid, client=client)
        spaces = []
        for space_data in response:
            space = Space(name=space_data["entity"]["name"], guid=space_data["metadata"]["guid"], org_guid=self.guid)
            spaces.append(space)
        return spaces

    # -------------------------------- cf api -------------------------------- #

    @classmethod
    def cf_api_get_list(cls):
        response = cf.cf_api_get_orgs()
        org_list = []
        for org_info in response:
            org_list.append(cls(name=org_info["entity"]["name"], guid=org_info["metadata"]["guid"]))
        return org_list

    def cf_api_get_spaces(self):
        response = cf.cf_api_get_org_spaces(self.guid)
        spaces = []
        for space_data in response:
            space = Space(space_data["entity"]["name"], space_data["metadata"]["guid"], self.guid)
            spaces.append(space)
        return spaces

    def cf_api_get_apps_and_services(self, client=None):
        """Return aggregated space summary for all spaces in the organization"""
        spaces = self.api_get_spaces(client=client)
        org_apps = []
        org_services = []
        for space in spaces:
            apps, services = space.cf_api_get_space_summary()
            org_apps.extend(apps)
            org_services.extend(services)
        return org_apps, org_services

    @retry(UnexpectedResponseError, tries=2, delay=5)
    def cf_api_delete(self):
        cf.cf_api_delete_org(self.guid)

    @classmethod
    def cf_api_tear_down_test_orgs(cls):
        """Use this method in tearDown and tearDownClass."""
        while len(cls.TEST_ORGS) > 0:
            test_org = cls.TEST_ORGS.pop()
            try:
                test_org.cf_api_delete()
            except UnexpectedResponseError as e:
                logger.warning("Failed to delete {}: {}".format(test_org, e.error_message))
