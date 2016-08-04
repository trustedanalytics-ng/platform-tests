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
from modules.constants import TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from modules.constants import HttpStatus


def _get_client(api_version=config.ng_component_api_version):
    configuration = K8sServiceConfigurationProvider.get(TapComponent.blob_store.value,
                                                        api_endpoint="api/{}".format(api_version))
    return HttpClientFactory.get(configuration)


def get_blob(blob_id, api_version=config.ng_component_api_version):
    """ GET /blobs/{blob_id} """
    response = _get_client(api_version).request(HttpMethod.GET,
                                                path="blobs/{}".format(blob_id),
                                                raw_response_with_exception=True,
                                                msg="BLOB-STORE: get blob")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def create_blob(blob_id, file_path):
    """ POST /blobs """
    file = {"uploadfile": (file_path, "multipart/form-data")}
    params = {"blob_id": blob_id}

    response = _get_client().request(HttpMethod.POST,
                                     path="blobs",
                                     params=params,
                                     files=file,
                                     raw_response_with_exception=True,
                                     msg="BLOB-STORE: create blob")
    assert response.status_code == HttpStatus.CODE_CREATED
    return response


def delete_blob(blob_id):
    """ DELETE /blobs/{blob_id} """
    response = _get_client().request(HttpMethod.DELETE, path="blobs/{}".format(blob_id),
                                     msg="BLOB-STORE: delete blob")
    return response

