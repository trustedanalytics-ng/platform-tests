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

from modules.constants import TapComponent
from modules.tap_object_model import Application


class _DynamicConfig(object):

    __config = {}

    def get(self, attribute_name):
        if attribute_name not in self.__config:
            getattr(self, attribute_name)()
        return self.__config[attribute_name]

    def uaa_auth(self) -> tuple:
        """
        Retrieves uaa credentials (username and password) from user-management env.
        """
        apps = Application.cf_api_get_list()
        user_management = next(a for a in apps if a.name == TapComponent.user_management.value)
        user_management_env = user_management.cf_api_env()
        upsi = user_management_env["VCAP_SERVICES"]["user-provided"]
        sso = next(x for x in upsi if x["name"] == "sso")
        uaa_login = sso["credentials"]["clientId"]
        uaa_password = sso["credentials"]["clientSecret"]
        self.__config["uaa_auth"] = (uaa_login, uaa_password)


dynamic_config = _DynamicConfig()
