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

from .ssh_client import CdhMasterSshClient
from .tap_logger import get_logger
from . import kerberos


logger = get_logger(__name__)


class Hive(object):
    __JDBC_URL = "jdbc:hive2://cdh-master-0:10000/default"
    __JDBC_KERBEROS_PARAMS = ";principal=hive/cdh-master-0@CLOUDERA;auth=kerberos"

    def __init__(self):
        self.__ssh_client = CdhMasterSshClient()
        self.__ssh_client.connect()

        self.__is_kerberos = kerberos.is_kerberos_environment()
        self.__url = self.__get_url()
        if self.__is_kerberos:
            kerberos.authenticate(self.__ssh_client)

    def __get_url(self):
        url = self.__JDBC_URL
        if self.__is_kerberos:
            url += self.__JDBC_KERBEROS_PARAMS
        return url

    def __ensure_quote(self, query):
        query = query.strip()
        if query[0] not in "'\"":
            query = "'{}'".format(query)
        return query

    def __get_cmd(self, *params):
        return ("beeline", "-u", "'{}'".format(self.__url), "--showHeader=false", "--outputformat=csv2") + params

    def exec_query(self, query):
        ssh_cmd = self.__ssh_client.exec_command_interactive(self.__get_cmd("-e", self.__ensure_quote(query)))
        ssh_cmd.assert_return_code_ok()
        return ssh_cmd.get_stdout_as_str()

    def close(self):
        self.__ssh_client.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
