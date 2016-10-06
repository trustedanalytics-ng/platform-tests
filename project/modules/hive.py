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

import config
from . import kerberos
from .http_client.configuration_provider.uaa import UaaConfigurationProvider
from .http_client.http_client_factory import HttpClientFactory
from .tap_logger import get_logger
from .tap_object_model import User

logger = get_logger(__name__)


class Hive(object):
    __JDBC_URL = "jdbc:hive2://cdh-master-0:10000/default"
    __JDBC_KERBEROS_PARAMS = ";principal=hive/cdh-master-0@CLOUDERA;auth=kerberos"

    def __init__(self, user=None):
        raise NotImplementedError("Will be refactored in DPNG-8899")
        self.__is_kerberos = kerberos.is_kerberos_environment()
        self.__url = self.__get_url()
        if user is None:
            user = User.get_admin()
        self.__user = user

    def __get_url(self):
        url = self.__JDBC_URL
        if self.__is_kerberos:
            url += self.__JDBC_KERBEROS_PARAMS
        return url

    def exec_query(self, query):
        cmds = [["beeline", "-n", "hive", "-u", "'{}'".format(self.__url), "--showHeader=false", "--outputformat=csv2", "-e", query]]

        if self.__is_kerberos:
            client = HttpClientFactory.get(UaaConfigurationProvider.get(self.__user.username, self.__user.password))
            cmds.insert(0, ["ktinit", "-t", client.auth.token])
        else:
            cmds[0] = ["sudo", "-u", self.__user.guid] + cmds[0]

        return CdhMasterClient(config.cdh_master_2_hostname).exec_commands(cmds)[-1][0].split()


