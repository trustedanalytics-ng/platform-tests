#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ...http_client import HttpMethod, HttpClientFactory
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider


def get_models(*, org_guid, client=None):
    """GET /models"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="models",
        params={"orgId": org_guid},
        msg="PLATFORM: list models"
    )


def insert_model(*, org_guid, name=None, creation_tool=None, revision=None, algorithm=None, description=None,
                 added_by=None, added_on=None, modified_by=None, modified_on=None, client=None):
    """POST /models"""
    body = {
        'name': name,
        'creationTool': creation_tool,
        'revision': revision,
        'algorithm': algorithm,
        'description': description,
        'addedBy': added_by,
        'addedOn': added_on,
        'modifiedBy': modified_by,
        'modifiedOn': modified_on
    }
    body = {k: v for k, v in body.items() if v is not None}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="models",
        params={"orgId": org_guid},
        body=body,
        msg="PLATFORM: insert model"
    )


def get_model_metadata(*, model_id, client=None):
    """GET /models/{model_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="models/{}".format(model_id),
        msg="PLATFORM: get metadata of model"
    )


def update_model(*, model_id, name=None, creation_tool=None, revision=None, algorithm=None, description=None,
                 added_by=None, added_on=None, modified_by=None, modified_on=None, client=None):
    """PUT /models/{model_id}"""
    body = {
        'name': name,
        'creationTool': creation_tool,
        'revision': revision,
        'algorithm': algorithm,
        'description': description,
        'addedBy': added_by,
        'addedOn': added_on,
        'modifiedBy': modified_by,
        'modifiedOn': modified_on
    }
    body = {k: v for k, v in body.items() if v is not None}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.PUT,
        path="models/{}".format(model_id),
        body=body,
        msg="PLATFORM: update model"
    )


def delete_model(*, model_id, client=None):
    """DELETE /models/{model_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="models/{}".format(model_id),
        msg="PLATFORM: delete model"
    )


def update_model_fields(*, model_id, name=None, creation_tool=None, revision=None, algorithm=None, description=None,
                        added_by=None, added_on=None, modified_by=None, modified_on=None, client=None):
    """PATCH /models/{model_id}"""
    body = {
        'name': name,
        'creationTool': creation_tool,
        'revision': revision,
        'algorithm': algorithm,
        'description': description,
        'addedBy': added_by,
        'addedOn': added_on,
        'modifiedBy': modified_by,
        'modifiedOn': modified_on
    }
    body = {k: v for k, v in body.items() if v is not None}
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.PATCH,
        path="models/{}".format(model_id),
        body=body,
        msg="PLATFORM: update model fields"
    )


def upload_model_artifact(model_id, artifact=None, client=None):
    """POST /models/{model_id}/artifacts"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="models/{}/artifacts".format(model_id),
        body=artifact,
        msg="PLATFORM: upload model artifact"
    )


def get_model_artifact_metadata(model_id, artifact_id, client=None):
    """GET /models/{model_id}/artifacts/{artifact_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="models/{}/artifacts/{}".format(model_id, artifact_id),
        msg="PLATFORM: get model artifact metadata"
    )


def get_model_artifact_file(model_id, artifact_id, client=None):
    """GET /models/{model_id}/artifacts/{artifact_id}/file"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="models/{}/artifacts/{}/file".format(model_id, artifact_id),
        msg="PLATFORM: download model artifact file"
    )


def delete_model_artifact(model_id, artifact_id, client=None):
    """DELETE /models/{model_id}/artifacts/{artifact_id}"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.DELETE,
        path="models/{}/artifacts/{}".format(model_id, artifact_id),
        msg="PLATFORM: delete model artifact metadata and file"
    )

