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

from .uaa_credentials_provider import UaaCredentialsProvider
from ..http_client.client_auth.http_method import HttpMethod
from ..http_client.http_client_factory import HttpClientFactory


def uaa_api_user_delete(user_id):
    """DELETE /users/{id}"""
    HttpClientFactory.get(UaaCredentialsProvider.get()).request(
        method=HttpMethod.DELETE,
        path="Users/{}".format(user_id),
        msg="UAA: delete user"
    )
