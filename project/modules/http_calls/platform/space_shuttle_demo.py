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
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.http_client_type import HttpClientType


def post_samples(space_shuttle_app, interval, interval_start):
    """POST rest/space-shuttle/samples"""
    console_client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
    configuration = HttpClientConfiguration(client_type=HttpClientType.CONSOLE,
                                            url="http://{}".format(space_shuttle_app.urls[0]),
                                            username=config.admin_username,
                                            password=config.admin_password)
    client = HttpClientFactory.get(configuration)
    client.session = console_client.session

    params = {'intervalLength': interval, 'intervalStart': interval_start}

    samples_data = client.request(
        method=HttpMethod.POST,
        path="rest/space-shuttle/samples",
        params=params,
        msg="POST space shuttle samples"
    )

    return samples_data
