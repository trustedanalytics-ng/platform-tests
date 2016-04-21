#
# Copyright (c) 2016 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from .data_science import DataScience
from ..constants import ServiceLabels


class Gearpump(object):

    def __init__(self, org_guid, space_guid, service_plan_name, instance_name=None, params=None):
        """Create Gearpump service instance"""
        self.data_science = DataScience(org_guid=org_guid, space_guid=space_guid,
                                        service_label=ServiceLabels.GEARPUMP, service_plan_name=service_plan_name,
                                        instance_name=instance_name, params=params)

    def login(self):
        self.data_science.request(
            method="POST",
            instance_url=self.data_science.instance_url,
            endpoint="login",
            username="Gearpump Client",
            data={"username": self.data_science.login, "password": self.data_science.password},
            message_on_error="Failed login to Gearpump UI")

    def submit_application_jar(self, jar_file, application_name):
        """Response returns only: {"success":true/false}"""
        endpoint = "api/v1.0/master/submitapp"
        files = {'jar': open(jar_file, 'rb')}
        response = self.data_science.request(
            method="POST",
            instance_url=self.data_science.instance_url,
            endpoint=endpoint,
            username="Gearpump Client",
            files=files,
            message_on_error="Failed submit application")
        if response["success"]:
            return GearpumpApplication(application_name, self.data_science)


class GearpumpApplication(object):

    def __init__(self, application_name, data_science):
        self.data_science = data_science
        self.app_id = None
        self.app_name = application_name
        self.app_status = None
        self.fill_application_details()

    def fill_application_details(self):
        endpoint = "api/v1.0/master/applist"
        response = self.data_science.request(
            method="GET",
            instance_url=self.data_science.instance_url,
            endpoint=endpoint,
            username="Gearpump Client",
            message_on_error="Failed get list of applications from Gearpump UI")
        for application in response["appMasters"]:
            if application["appName"] == self.app_name:
                self.app_id = application["appId"]
                self.app_status = application["status"]

    def kill_application(self):
        endpoint = "api/v1.0/appmaster/" + str(self.app_id)
        self.data_science.request(
            method="DELETE",
            instance_url=self.data_science.instance_url,
            endpoint=endpoint,
            username="Gearpump Client",
            message_on_error="Failed killing application on Gearpump UI")
        """Update application details"""
        self.fill_application_details()

    @property
    def is_started(self):
        return self.app_status == "active"
