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

import pytest

from modules.tap_logger import log_fixture
from modules.tap_object_model import CatalogTemplate, CatalogImage, CatalogApplication, CatalogService


pytestmark = [pytest.mark.usefixtures("open_tunnel")]


@pytest.fixture(scope="session")
def catalog_template(session_context):
    log_fixture("Create sample template in catalog")
    return CatalogTemplate.create(session_context)


@pytest.fixture(scope="session")
def catalog_image(session_context):
    log_fixture("Create sample image in catalog")
    return CatalogImage.create(session_context)


@pytest.fixture(scope="session")
def catalog_application(session_context, catalog_template, catalog_image):
    log_fixture("Create sample application in catalog")
    return CatalogApplication.create(session_context, template_id=catalog_template.id, image_id=catalog_image.id)


@pytest.fixture(scope="session")
def catalog_service(session_context, catalog_template):
    log_fixture("Create sample service in catalog")
    return CatalogService.create(session_context, template_id=catalog_template.id)