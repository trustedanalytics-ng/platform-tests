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
import modules.tap_object_model.model_artifact as artifact


@functools.total_ordering
class ScoringEngineModel(object):
    _COMPARABLE_ATTRIBUTES = ["id", "name", "description", "revision", "algorithm", "creation_tool"]
    _UPDATABLE_METADATA = ["name", "description", "creation_tool", "revision", "algorithm"]

    def __init__(self, *, model_id, name, description, revision, algorithm, creation_tool, artifacts, added_by,
                 added_on, modified_by, modified_on):
        self.id = model_id
        self.name = name
        self.description = description
        self.revision = revision
        self.algorithm = algorithm
        self.creation_tool = creation_tool
        self.artifacts = artifacts
        self.added_by = added_by
        self.added_on = added_on
        self.modified_by = modified_by
        self.modified_on = modified_on

    def __repr__(self):
        return "{} (name={}, id={})".format(self.__class__.__name__, self.name, self.id)

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._COMPARABLE_ATTRIBUTES)

    def __lt__(self, other):
        return self.id < other.id

    @classmethod
    def _from_response(cls, response):
        model = cls(model_id=response.get("id"), name=response.get("name"), description=response.get("description"),
                    revision=response.get("revision"), algorithm=response.get("algorithm"),
                    creation_tool=response.get("creationTool"), artifacts=response.get("artifacts"),
                    added_by=response.get("addedBy"), added_on=response.get("addedOn"),
                    modified_by=response.get("modifiedBy"), modified_on=response.get("modifiedOn"))
        return model

    @classmethod
    def get_list(cls, org_guid, client=None):
        response = model_catalog_api.get_models(org_guid=org_guid, client=client)
        models = []
        for model_data in response:
            model = cls._from_response(response=model_data)
            models.append(model)
        return models

    @classmethod
    def create(cls, context, *, org_guid, description=None, name=None, creation_tool=None, revision=None,
               algorithm=None, artifacts=None, added_by=None, added_on=None, modified_by=None, modified_on=None,
               client=None):
        response = model_catalog_api.insert_model(org_guid=org_guid, name=name, creation_tool=creation_tool,
                                                  revision=revision, algorithm=algorithm, description=description,
                                                  artifacts=artifacts, added_by=added_by, added_on=added_on,
                                                  modified_by=modified_by, modified_on=modified_on, client=client)
        new_model = cls._from_response(response=response)
        context.test_objects.append(new_model)
        return new_model

    @classmethod
    def get(cls, *, model_id, client=None):
        response = model_catalog_api.get_model_metadata(model_id=model_id, client=client)
        return cls._from_response(response)

    def update(self, *, name=None, description=None, creation_tool=None, revision=None, algorithm=None, artifacts=None,
               added_by=None, added_on=None, modified_by=None, modified_on=None, client=None):
        for attribute_name in self._UPDATABLE_METADATA:
            setattr(self, attribute_name, locals()[attribute_name])
        model_catalog_api.update_model(model_id=self.id, name=name, description=description,
                                       creation_tool=creation_tool, revision=revision, algorithm=algorithm,
                                       artifacts=artifacts, added_by=added_by, added_on=added_on,
                                       modified_by=modified_by, modified_on=modified_on, client=client)

    def delete(self, *, client=None):
        model_catalog_api.delete_model(model_id=self.id, client=client)

    def patch(self, *, name=None, description=None, creation_tool=None, revision=None, algorithm=None, artifacts=None,
              added_by=None, added_on=None, modified_by=None, modified_on=None, client=None):
        for attribute_name in self._UPDATABLE_METADATA:
            if locals()[attribute_name] is not None:
                setattr(self, attribute_name, locals()[attribute_name])
        model_catalog_api.update_model_fields(model_id=self.id, name=name, creation_tool=creation_tool,
                                              revision=revision, algorithm=algorithm, description=description,
                                              artifacts=artifacts, added_by=added_by, added_on=added_on,
                                              modified_by=modified_by, modified_on=modified_on, client=client)

    def cleanup(self):
        self.delete()



