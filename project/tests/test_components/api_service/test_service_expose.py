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
import uuid
import pytest
import modules.http_calls.platform.api_service as api
from fixtures.k8s_templates import template_example
from modules.constants import ApiServiceHttpStatus
from modules.tap_logger import step
from modules.tap_object_model import ServiceOffering, ServiceInstance, Application
from tests.fixtures.assertions import assert_raises_http_exception


class TestServiceExpose:

    @pytest.fixture(scope="function")
    def offering_from_python_app(self, context, api_service_admin_client, sample_python_app):
        app = sample_python_app
        image = Application.get_image(app_inst_id=app.id, client=api_service_admin_client)
        offering_json = template_example.sample_python_app_offering
        offering_json['body']['deployments'][0]['spec']['template']['spec']['containers'][0]['image'] = image
        offering = ServiceOffering.create(context, client=api_service_admin_client,
                                          template_body=offering_json['body'])
        service = ServiceInstance.create_with_name(context, offering_label=offering.label,
                                                   plan_name=offering.service_plans[0].name)
        ServiceInstance.ensure_running(service, client=api_service_admin_client)
        return service

    def test_expose_and_unexpose_urls(self, api_service_admin_client, offering_from_python_app):
        """ Verify if is it possible to expose, unexpose service instance URLS, exposed URLS responds.

            Push sample app, create new offering using image of sample app and create service instance of new offering.
            Expose service instance URLS, then tests assert that URLS responds and present in service instance
            credentials. After it unexpose URLS and verify if it is not in service credentials.

            Input data:
                Python application: application which is pushed on platform

            Expected results:
                It is possible to create new offering using image of pushed application. Service instance can be
                 exposed. Exposed URLS responds and present in service instance credentials.

            Steps:
                1. Create instance of new offering
                2. Expose URLS and check if responds
                3. Get credentials and verify if contains exposed URLS
                4. Unexpose URLS and verify if URLS are not in credentials
        """
        step("Create offering from sample_python_app")
        service = offering_from_python_app
        step("Expose urls")
        urls = ServiceInstance.expose_urls(service_id=service.id, client=api_service_admin_client)
        url = ('http://{}'.format(urls[0]))
        ServiceInstance.ensure_responding(url=url)
        step("Get credentials and check that contains urls")
        credentials = ServiceInstance.get_credentials(service.id, api_service_admin_client)
        assert urls[0] in str(credentials)
        step("Unexpose urls")
        unexpose = ServiceInstance.expose_urls(service_id=service.id, client=api_service_admin_client,
                                               should_expose=False)
        credentials = ServiceInstance.get_credentials(service.id, api_service_admin_client)
        assert urls[0] not in unexpose, str(credentials)

    @pytest.mark.bugs("DPNG-13253 - Code 500 when exposing twice the same service")
    def test_expose_urls_twice(self, api_service_admin_client, offering_from_python_app):
        """ Verify if try to expose exposed service results conflict.

            Push sample app, create new offering using image of sample app and create service instance of new offering.
            Expose service instance URLS and try to expose URLS once again.

            Input data:
                Offering: offering created based on python application image

            Expected results:
                It is possible to expose service URLS, second try results conflict (409 Conflict).

            Steps:
                1. Create instance of new offering
                2. Expose URLS
                3. Try to expose URLS once again
        """
        step("Create offering from sample_python_app")
        service = offering_from_python_app
        step("Expose urls")
        ServiceInstance.expose_urls(service_id=service.id, client=api_service_admin_client)
        step("Try to expose urls once again")
        assert_raises_http_exception(status=ApiServiceHttpStatus.CODE_CONFLICT,
                                     callableObj=ServiceInstance.expose_urls, error_message_phrase='already exists',
                                     client=api_service_admin_client, service_id=service.id)

    def test_unexpose_urls_twice(self, api_service_admin_client, offering_from_python_app):
        """ Verify if try to unexpose not exposed service results error.

            Push sample app, create new offering using image of sample app and create service instance of new offering.
            Expose service instance URLS and try to unexpose URLS once again.

            Input data:
                Offering: offering created based on python application image

            Expected results:
                It is possible to unexpose service URLS, second try results error (404 Not Found).

            Steps:
                1. Create instance of new offering
                2. Expose URLS
                3. Unxpose URLS
                4. Try to unexpose URLS once again
        """
        step("Create offering from sample_python_app")
        service = offering_from_python_app
        step("Expose urls")
        api.expose_service(client=api_service_admin_client, service_id=service.id)
        step("Unexpose urls")
        api.expose_service(client=api_service_admin_client, service_id=service.id, should_expose=False)
        step("Unexpose urls once again")
        assert_raises_http_exception(status=ApiServiceHttpStatus.CODE_NOT_FOUND,
                                     callableObj=ServiceInstance.expose_urls,
                                     error_message_phrase='not found',
                                     client=api_service_admin_client, service_id=service.id, should_expose=False)

    def test_expose_non_existing_service(self, api_service_admin_client, offering_from_python_app):
        """ Verify if try to expose non existing service instance results error

            Push sample app, create new offering using image of sample app and create service instance of new offering.
            Try to expose non existing service instance.

            Input data:
                Offering: offering created based on python application image
                Not existing instance id: created id to expose try

            Expected results:
                Try to expose non existing service instance results error (404 Not Found)

            Steps:
                1. Create instance of new offering
                2. Try to expose non existing service instance
        """
        step("Create offering from sample_python_app")
        offering_from_python_app
        step("Create invalid service id")
        guid = uuid.uuid4()
        step("Expose urls using invalid service id")
        assert_raises_http_exception(status=ApiServiceHttpStatus.CODE_NOT_FOUND,
                                     callableObj=ServiceInstance.expose_urls,
                                     error_message_phrase='not found',
                                     client=api_service_admin_client, service_id=guid)
