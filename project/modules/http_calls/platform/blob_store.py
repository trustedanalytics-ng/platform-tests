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

from tap_component_config import TAP_core_services
from modules.constants import HttpStatus, TapComponent
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider


def _get_client():
    api_version = TAP_core_services[TapComponent.blob_store]["api_version"]
    configuration = K8sServiceConfigurationProvider.get(TapComponent.blob_store,
                                                        api_endpoint="api/{}".format(api_version))
    return HttpClientFactory.get(configuration)


def get_blob(*, blob_id):
    """ GET /blobs/{blob_id} """
    response = _get_client().request(method=HttpMethod.GET,
                                     path="blobs/{}".format(blob_id),
                                     raw_response=True, raise_exception=True,
                                     msg="BLOB-STORE: get blob")
    assert response.status_code == HttpStatus.CODE_OK
    return response


def create_blob_raw_params(*, files, params):
    """ POST /blobs """
    response = _get_client().request(method=HttpMethod.POST,
                                     path="blobs",
                                     params=params,
                                     files=files,
                                     raw_response=True, raise_exception=True,
                                     msg="BLOB-STORE: create blob")
    assert response.status_code == HttpStatus.CODE_CREATED
    return response


def create_blob_from_file(*, blob_id, file_path):
    files = {"uploadfile": (file_path, open(file_path, "rb"))}
    params = {"blob_id": blob_id}
    return create_blob_raw_params(files=files, params=params)


def create_blob_from_data(*, blob_id, blob_content):
    files = {"uploadfile": blob_content}
    params = {"blob_id": blob_id}
    return create_blob_raw_params(files=files, params=params)


def delete_blob(*, blob_id):
    """ DELETE /blobs/{blob_id} """
    response = _get_client().request(method=HttpMethod.DELETE,
                                     path="blobs/{}".format(blob_id),
                                     msg="BLOB-STORE: delete blob")
    return response

