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

from modules.constants import ServiceLabels
from modules.http_calls import orientdb_dashboard


class OrientDbDashboardApi(object):
    """OrientDB Dashboard application API."""
    def __init__(self, orientdb_dashboard_app, orientdb_api_app):
        self.url = "http://{}".format(orientdb_dashboard_app.urls[0])
        self.password = orientdb_api_app.get_credentials(service_name=ServiceLabels.ORIENT_DB)["password"]

    def get_database_names(self):
        """Return databases."""
        databases = orientdb_dashboard.get_databases(app_url=self.url)
        return databases["databases"]

    def get_database_info(self, database_name):
        """Return database info."""
        return orientdb_dashboard.get_database(database_name=database_name, password=self.password, app_url=self.url)

    def get_user_roles(self, database_name):
        """Return a dict mapping role_name to status"""
        result = self._execute_command(database_name, command="select * from oUser fetchPlan *:1")
        return {result["result"][i]['name']: result["result"][i]['status'] for i in range(0, len(result["result"]))}

    def select_from_class(self, database_name, class_name):
        """Return content of class."""
        result = self._execute_command(database_name, command="select from {};".format(class_name))
        return result["result"]

    def _execute_command(self, database_name, command):
        """Executes command in OrientDB Dashboard application."""
        return orientdb_dashboard.execute_command(database_name=database_name, command=command,
                                                  password=self.password, app_url=self.url)
