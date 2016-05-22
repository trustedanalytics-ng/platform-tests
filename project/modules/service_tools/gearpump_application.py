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

from ..http_client.http_client import HttpClient
from ..http_client.client_auth.http_method import HttpMethod


class GearpumpApplication(object):
    """Gearpump application instance."""

    def __init__(self, name, client: HttpClient):
        self.client = client
        self.app_name = name
        self.app_status = None
        self.app_id = None
        self.fill_application_details()

    def fill_application_details(self):
        """Set application id and status."""
        response = self.client.request(
            method=HttpMethod.GET,
            path="api/v1.0/master/applist",
            msg="Gearpump: get list of applications"
        )
        for application in response["appMasters"]:
            if application["appName"] == self.app_name:
                self.app_id = application["appId"]
                self.app_status = application["status"]

    def kill_application(self):
        """Kill application and refresh application details."""
        self.client.request(
            method=HttpMethod.DELETE,
            path="api/v1.0/appmaster/{}".format(self.app_id),
            msg="Gearpump: kill application {}".format(self.app_id)
        )
        self.fill_application_details()

    @property
    def is_started(self) -> bool:
        """Check if application is started."""
        return self.app_status == "active"
