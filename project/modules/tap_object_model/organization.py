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

from ..constants import UserManagementHttpStatus
from ..exceptions import UnexpectedResponseError
from ..http_calls import cloud_foundry as cf
from ..http_calls.platform import metrics_provider, user_management
from ..test_names import generate_test_object_name


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
    def api_create(cls, context, name=None, client=None, delete_on_fail=True):
        if name is None:
            name = generate_test_object_name()
        try:
            response = user_management.api_create_organization(name, client=client)
        except UnexpectedResponseError as e:
            # If exception occurred, check whether org is on the list and if so, delete it.
            if delete_on_fail:
                org = next((o for o in cls.api_get_list() if o.name == name), None)
                if org is not None:
                    org.cleanup()
            raise
        org = cls(name=name, guid=response)
        context.orgs.append(org)
        return org

    @classmethod
    def api_get_list(cls, client=None):
        response = user_management.api_get_organizations(client=client)
        organizations = []
        for organization_data in response:
            org = cls(name=organization_data["name"], guid=organization_data["guid"])
            organizations.append(org)
        return organizations

    def rename(self, new_name, client=None):
        self.name = new_name
        return user_management.api_rename_organization(self.guid, new_name, client=client)

    def api_delete(self, client=None):
        user_management.api_delete_organization(self.guid, client=client)

    def api_get_metrics(self, client=None):
        self.metrics = metrics_provider.api_get_org_metrics(self.guid, client=client)

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

    def cleanup(self):
        self.cf_api_delete()
