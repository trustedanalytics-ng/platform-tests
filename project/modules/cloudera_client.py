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

import requests

from configuration.config import CONFIG
from .ssh_client import CdhManagerSshTunnel


class ClouderaClient(object):
    def __init__(self):
        self.tunnel = CdhManagerSshTunnel()
        self.tunnel.connect()

    def api_client_config(self, service_name):
        """Returns zip-compressed archive of the client configuration."""
        r = requests.get(
            "http://localhost:1234/api/v10/clusters/CDH-cluster/services/{}/clientConfig".format(service_name),
            auth=(CONFIG["cloudera_username"], CONFIG["cloudera_password"])
        )
        r.raise_for_status()
        return r.content

    def close(self):
        self.tunnel.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
