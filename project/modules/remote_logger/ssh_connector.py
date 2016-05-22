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

from ..constants.logger_type import LoggerType
from ..tap_logger import get_logger
from ..ssh_client import SshTunnel
from .config import Config

logger = get_logger(LoggerType.REMOTE_LOGGER)


class SshConnector(object):
    """ Remote logger ssh connection manager. """

    def __init__(self):
        self.__ssh_tunnel = None

    def open_ssh_tunnel(self):
        """ Open ssh tunnel. """
        try:
            logger.info("Create ssh tunnel")
            self.__create_ssh_tunnel()
            logger.info("Open ssh tunnel")
            self.__ssh_tunnel.connect()
        except:
            raise SshConnectorException()

    def close_ssh_tunnel(self):
        """ Close ssh tunnel if opened. """
        if self.__ssh_tunnel is None:
            return
        logger.info("Close ssh tunnel")
        self.__ssh_tunnel.disconnect()
        self.__ssh_tunnel = None

    def __create_ssh_tunnel(self):
        """ Create ssh tunnel. """
        if self.__ssh_tunnel is not None:
            return
        self.__ssh_tunnel = SshTunnel(
            hostname=Config.ELASTIC_SEARCH_HOST,
            port=Config.ELASTIC_SEARCH_PORT,
            username=Config.ELASTIC_SSH_TUNNEL_USER,
            path_to_key=Config.JUMPBOX_KEY_PATH,
            via_hostname=Config.JUMPBOX_HOST,
            local_port=Config.ELASTIC_SEARCH_PORT
        )


class SshConnectorException(Exception):
    def __init__(self):
        super().__init__("Failed to open ssh tunnel.")
