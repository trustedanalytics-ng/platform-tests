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

import functools

import modules.http_calls.platform.model_catalog as model_catalog_api


@functools.total_ordering
class ModelArtifact(object):

    _COMPARABLE_ATTRIBUTES = ["id", "location", "filename", "actions"]
    _UPDATABLE_METADATA = ["filename", "actions"]

    ARTIFACT_ACTIONS = {
        "publish_tap_scoring_engine": "PUBLISH_TAP_SCORING_ENGINE",
        "publish_jar_scoring_engine": "PUBLISH_JAR_SCORING_ENGINE"
    }

    def __init__(self, *, artifact_id, filename, actions, location):
        self.id = artifact_id
        self.filename = filename
        self.actions = actions
        self.location = location

    def __repr__(self):
        return "{} (filename={}, id={})".format(self.__class__.__name__, self.filename, self.id)

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    @classmethod
    def _from_response(cls, response):
        artifact = cls(artifact_id=response.get("id"), filename=response.get("filename"),
                       location=response.get("location"), actions=response.get("actions"))
        return artifact

    @classmethod
    def upload_artifact(cls, model_id, filename=None, actions=None, client=None):
        response = model_catalog_api.upload_model_artifact(model_id=model_id, filename=filename, actions=actions,
                                                           client=client)
        return cls._from_response(response)

    @classmethod
    def get_artifact(cls, model_id, artifact_id, client=None):
        response = model_catalog_api.get_model_artifact_metadata(model_id=model_id, artifact_id=artifact_id,
                                                                 client=client)
        return response

    @classmethod
    def get_artifact_file(cls, model_id, artifact_id, client=None):
        response = model_catalog_api.get_model_artifact_file(model_id=model_id, artifact_id=artifact_id,
                                                             client=client)
        return response

    @classmethod
    def delete_artifact(cls, model_id, artifact_id, client=None):
        model_catalog_api.delete_model_artifact(model_id=model_id, artifact_id=artifact_id, client=client)