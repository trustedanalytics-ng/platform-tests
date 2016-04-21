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

import functools

from . import Application, ServiceInstance
from ..tap_logger import get_logger
from ..test_names import get_test_name
from ..http_calls import cloud_foundry as cf, platform as api


logger = get_logger(__name__)


@functools.total_ordering
class Space(object):
    NAME_PREFIX = "test_space_"

    def __init__(self, name, guid=None, org_guid=None):
        self.name = name
        self.guid = guid
        self.org_guid = org_guid

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def api_create(cls, org, name=None, client=None):
        name = get_test_name() if name is None else name
        response = api.api_create_space(org.guid, name, client=client)
        space = cls(name=name, guid=response, org_guid=org.guid)
        return space

    @classmethod
    def api_get_list(cls, client=None):
        response = api.api_get_spaces(client)
        spaces = []
        for space_data in response:
            org_guid = space_data["entity"]["organization_guid"]
            name = space_data["entity"]["name"]
            guid = space_data["metadata"]["guid"]
            spaces.append(cls(name, guid, org_guid))
        return spaces

    def api_delete(self, client=None):
        api.api_delete_space(self.guid, client=client)

    # -------------------------------- cf api -------------------------------- #

    def cf_api_get_space_summary(self):
        """Return tuple with list of Application and ServiceInstance objects."""
        response = cf.cf_api_space_summary(self.guid)
        apps = Application.from_cf_api_space_summary_response(response, self.guid)
        service_instances = []
        for si_data in response["services"]:
            try:
                service_label = si_data["service_plan"]["service"]["label"]
            except KeyError:
                service_label = None
            service_instances.append(ServiceInstance(guid=si_data["guid"], name=si_data["name"], space_guid=self.guid,
                                     service_label=service_label))
        return apps, service_instances

    @classmethod
    def cf_api_get_list(cls):
        response = cf.cf_api_get_spaces()
        spaces = []
        for space_data in response:
            org_guid = space_data["entity"]["organization_guid"]
            name = space_data["entity"]["name"]
            guid = space_data["metadata"]["guid"]
            spaces.append(cls(name, guid, org_guid))
        return spaces

    def cf_api_delete(self):
        cf.cf_api_delete_space(self.guid)
