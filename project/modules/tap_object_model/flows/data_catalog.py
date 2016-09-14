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

from .. import DataSet, Transfer


def create_dataset_from_link(context, org_guid, source, is_public=False, category=DataSet.CATEGORIES[0],
                             client=None) -> tuple:
    transfer = Transfer.api_create(context, org_guid=org_guid, source=source, category=category, is_public=is_public,
                                   client=client)
    transfer.ensure_finished()
    data_set = DataSet.api_get_matching_to_transfer(org_guid=org_guid, transfer_title=transfer.title, client=client)
    return transfer, data_set


def create_dataset_from_file(context, org_guid, file_path, client=None, category=None) -> tuple:
    transfer = Transfer.api_create_by_file_upload(context, org_guid=org_guid, file_path=file_path, category=category,
                                                  client=client)
    transfer.ensure_finished()
    data_set = DataSet.api_get_matching_to_transfer(org_guid=org_guid, transfer_title=transfer.title, client=client)
    return transfer, data_set


def create_datasets_from_links(context, org_guid, source_list, client=None):
    datasets = []
    for source in source_list:
        _, dataset = create_dataset_from_link(context, org_guid, source, client=client)
        datasets.append(dataset)
    return datasets
