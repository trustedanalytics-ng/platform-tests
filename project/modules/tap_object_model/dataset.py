#
# Copyright (c) 2015-2016 Intel Corporation
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
import datetime
from enum import Enum

from retry import retry

from ..http_calls.platform import data_catalog, dataset_publisher


class DatasetAccess(Enum):
    PUBLIC = True
    PRIVATE = False


@functools.total_ordering
class DataSet(object):

    COMPARABLE_ATTRIBUTES = ["category", "creation_time", "data_sample", "format", "is_public", "id",
                             "org_guid", "record_count", "size", "source_uri", "target_uri", "title"]
    CATEGORIES = ["other", "agriculture", "climate", "science", "energy", "business", "consumer", "education",
                  "finance", "manufacturing", "ecosystems", "health"]
    FILE_FORMATS = ["CSV"]

    def __init__(self, category=None, creation_time=None, data_sample=None, format=None, id=None, is_public=None,
                 org_guid=None, record_count=None, size=None, source_uri=None, target_uri=None, title=None):
        self.category, self.creation_time, self.data_sample, self.format = category, creation_time, data_sample, format
        self.is_public, self.id, self.record_count, self.size = is_public, id, record_count, size
        self.source_uri, self.target_uri, self.title, self.org_guid = source_uri, target_uri, title, org_guid

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{0} (title={1}, id={2})".format(self.__class__.__name__, self.title, self.id)

    @classmethod
    def api_get_list(cls, org_list=None, query="", filters=(), size=100, time_from=0, only_private=False,
                     only_public=False, client=None):
        org_guids = None
        if org_list is not None:
            org_guids = [org.guid for org in org_list]
        response = data_catalog.api_get_datasets(org_guids, query, filters, size, time_from, only_private, only_public,
                                                 client=client)
        data_sets = []
        for data in response["hits"]:
            data_set = cls(id=data["id"], category=data["category"], title=data["title"], format=data["format"],
                           creation_time=data["creationTime"], is_public=data["isPublic"], org_guid=data["orgUUID"],
                           data_sample=data["dataSample"], record_count=data["recordCount"], size=data["size"],
                           source_uri=data["sourceUri"], target_uri=data["targetUri"])
            data_sets.append(data_set)
        return data_sets

    @classmethod
    def api_get_matching_to_transfer_list(cls, transfer_title_list, org_list=None, client=None):
        """Return datasets whose title is in transfer_title_list."""
        datasets = cls.api_get_list(org_list=org_list, client=client)
        return [ds for ds in datasets if ds.title in transfer_title_list]

    @classmethod
    @retry(AssertionError, tries=15, delay=2)
    def api_get_matching_to_transfer(cls, transfer_title, org, client=None):
        """Return dataset whose title matches transfer_title or raise AssertionError if such dataset is not found."""
        datasets = cls.api_get_matching_to_transfer_list(transfer_title_list=[transfer_title], org_list=[org],
                                                         client=client)
        dataset = next(iter(datasets), None)
        if dataset is None:
            raise AssertionError("Dataset {} was not found".format(transfer_title))
        return dataset

    @classmethod
    def api_get(cls, data_set_id, client=None):
        response = data_catalog.api_get_dataset(data_set_id, client)
        source = response["_source"]
        return cls(id=response["_id"], category=source["category"], title=source["title"], format=source["format"],
                   creation_time=source["creationTime"], is_public=source["isPublic"], org_guid=source["orgUUID"],
                   data_sample=source["dataSample"], record_count=source["recordCount"], size=source["size"],
                   source_uri=source["sourceUri"], target_uri=source["targetUri"])

    def api_publish(self, client=None):
        return dataset_publisher.api_publish_dataset(category=self.category, creation_time=self.creation_time,
                                                     data_sample=self.data_sample, format=self.format,
                                                     is_public=self.is_public, org_guid=self.org_guid,
                                                     record_count=self.record_count, size=self.size,
                                                     source_uri=self.source_uri, target_uri=self.target_uri,
                                                     title=self.title, client=client)

    def api_update(self, creation_time=None, target_uri=None, category=None, format=None, record_count=None,
                   is_public=None, org_guid=None, source_uri=None, size=None, data_sample=None, title=None,
                   client=None):
        data_catalog.api_update_dataset(self.id, creation_time, target_uri, category, format, record_count,
                                        is_public, org_guid, source_uri, size, data_sample, title, client)

    def api_delete(self, client=None):
        data_catalog.api_delete_dataset(self.id, client)

    def get_details(self):
        return dict(accessibility=DatasetAccess.PUBLIC.name if self.is_public else DatasetAccess.PRIVATE.name,
                    title=self.title, category=self.category, recordCount=self.record_count, sourceUri=self.source_uri,
                    size=self.size, orgUUID=self.org_guid, targetUri=self.target_uri, format=self.format,
                    dataSample=self.data_sample, isPublic=self.is_public,
                    creationTime=datetime.datetime.strptime(self.creation_time, "%Y-%m-%dT%H:%M:%S.%f")
                    .strftime("%Y-%m-%dT%H:%M"))
