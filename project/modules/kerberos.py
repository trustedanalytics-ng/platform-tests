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

from configuration.config import CONFIG
from .tap_logger import get_logger
from .file_utils import get_file_as_str_from_zip_archive, get_value_from_core_site_xml
from .cloudera_client import ClouderaClient


logger = get_logger(__name__)


CORE_SITE_XML = "hive-conf/core-site.xml"
HADOOP_SECURITY_AUTHENTICATION = "hadoop.security.authentication"
KERBEROS = "kerberos"
SERVICE = "HIVE"


def is_kerberos_environment():
    with ClouderaClient() as cc:
        xml = get_file_as_str_from_zip_archive(cc.api_client_config(SERVICE), CORE_SITE_XML)
        value = get_value_from_core_site_xml(xml, HADOOP_SECURITY_AUTHENTICATION)
        logger.info("%s=%s", HADOOP_SECURITY_AUTHENTICATION, value)
        return KERBEROS == value


def authenticate(ssh_client):
    ssh_cmd = ssh_client.exec_command_interactive(["kinit", CONFIG["kerberos_username"]])
    ssh_cmd.stdin.write(CONFIG["kerberos_password"] + "\n")
    ssh_cmd.assert_return_code_ok()
