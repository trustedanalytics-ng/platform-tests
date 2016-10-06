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

from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.cloudera import ClouderaConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory


class ClouderaClient(object):
    def __init__(self):
        raise NotImplementedError("Will be refactored in DPNG-9155")
        self.tunnel = ClouderaManagerSshTunnel()
        self.tunnel.connect()

    def api_client_config(self, service_name):
        """Returns zip-compressed archive of the client configuration."""
        r = HttpClientFactory.get(ClouderaConfigurationProvider.get("http://127.0.0.1:1234")).request(
            method=HttpMethod.GET,
            path="api/v10/clusters/CDH-cluster/services/{}/clientConfig".format(service_name),
            msg="CLOUDERA: get client config",
            raw_response=True
        )
        r.raise_for_status()
        return r.content

    def close(self):
        self.tunnel.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
