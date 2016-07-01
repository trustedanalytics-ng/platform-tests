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

from ..http_calls.platform import platform_snapshot


class PlatformSnapshot(object):

    comparable_attributes = ["id", "platform_version", "cf_version", "cdh_version", "created_at"]

    def __init__(self, id=None, platform_version=None, created_at=None, cdh_version=None, cf_version=None,
                 applications=None, cdh_services=None, cf_services=None):
        self.id = id
        self.platform_version = platform_version
        self.created_at = created_at
        self.cdh_version = cdh_version
        self.cf_version = cf_version
        self.applications = applications
        self.cdh_services = cdh_services
        self.cf_services = cf_services

    def __eq__(self, other):
        return all((getattr(self, name) == getattr(other, name) for name in self.comparable_attributes))

    @classmethod
    def _from_api_response(cls, version_data):
        return cls(
            id=version_data["id"],
            platform_version=version_data["platform_version"],
            created_at=version_data["created_at"],
            cdh_version=version_data["cdh_version"],
            cf_version=version_data["cf_version"],
            applications=version_data["applications"],
            cdh_services=version_data["cdh_services"],
            cf_services=version_data["cf_services"]
        )

    @classmethod
    def api_get_version(cls, client=None):
        response = platform_snapshot.api_get_version(client=client)
        return cls._from_api_response(response)

    @classmethod
    def api_get_snapshots(cls, client=None):
        response = platform_snapshot.api_get_snapshots(client=client)
        snapshots = []
        for snapshot in response:
            snap = cls._from_api_response(snapshot)
            snapshots.append(snap)
        return snapshots

    @classmethod
    def api_trigger_snapshots(cls, client=None):
        return platform_snapshot.api_trigger_snapshots(client=client)