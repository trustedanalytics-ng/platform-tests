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
import json

import pytest
import requests

from modules.constants import ServiceLabels, ServicePlan
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance


class TestElasticsearch:

    plans = [ServicePlan.SINGLE_SMALL, ServicePlan.SINGLE_MEDIUM]

    @pytest.mark.parametrize("plan", plans)
    def test_elasticsearch(self, context, api_service_admin_client, plan):
        """
        <b>Description:</b>
        Verify if it is possible to create instance of Elasticsearch-24 and do some operations on search engine.

        Test creates Elasticsearch-24 instance, expose URLs and check cluster health, insert some data, search in data,
        count inserted data using Elasticsearch-24 REST Api.

        <b>Input data:</b>
        1. Elasticsearch-24 instance
        2. Sample json data

        <b>Expected results:</b>
        It is possible to create Elasticsearch-24 instance, expose its URLs and operations like insert data, search in
        data, count data work properly.

        <b>Steps:</b>
        1. Create Elasticsearch-24 instance
        2. Check Elasticsearch-24 cluster health
        3. Insert sample data
        4. Get inserted data
        5. Search in inserted data
        6. Count inserted data
        7. Insert new data
        8. Count inserted data
        """
        sample_data_1 = {
            "user": "kimchy",
            "post_date": "2009-11-15T14:12:12",
            "message": "trying out Elasticsearch"
        }
        sample_data_2 = {
            "user": "greg",
            "post_date": "2009-12-11T22:22:22",
            "message": "inserting new data to Elasticsearch"
        }
        add_data_msg = "\"total\":1,\"successful\":1,\"failed\":0"
        step("Create elasticsearch instance")
        elasticsearch = ServiceInstance.create_with_name(context=context, offering_label=ServiceLabels.ELASTICSEARCH24,
                                                         plan_name=plan)
        elasticsearch.ensure_running(client=api_service_admin_client)
        urls = ServiceInstance.expose_urls(service_id=elasticsearch.id, client=api_service_admin_client)
        ServiceInstance.ensure_responding(url=urls[0])
        step("Check cluster health")
        response = requests.get(url="{}/_cluster/health".format(urls[0]))
        assert "\"status\":\"green\"", "\"number_of_nodes\":1" in str(response.content)
        step("Insert sample data")
        response = requests.put(url="{}/twitter/tweet/1".format(urls[0]), data=json.dumps(sample_data_1),
                                headers={'Content-Type': 'application/json'})
        assert add_data_msg in str(response.content)
        step("Get inserted data")
        requests.get(url="{}/twitter/_refresh".format(urls[0]))
        response = requests.get(url="{}/twitter/tweet/1".format(urls[0]))
        step("Search in data")
        response_search = requests.get(url="{}/twitter/_search?q=user:kimchy".format(urls[0]))
        for value in sample_data_1.values():
            assert value in str(response.content)
            assert value in str(response_search.content)
        step("Count inserted data")
        response = requests.get(url="{}/twitter/_count".format(urls[0]))
        assert "\"count\":1" in str(response.content)
        step("Insert new data")
        requests.put(url="{}/twitter/tweet/2".format(urls[0]), data=json.dumps(sample_data_2),
                     headers={'Content-Type': 'application/json'})
        requests.get(url="{}/twitter/_refresh".format(urls[0]))
        step("Count inserted data")
        response = requests.get(url="{}/twitter/_count".format(urls[0]))
        assert "\"count\":2" in str(response.content)
