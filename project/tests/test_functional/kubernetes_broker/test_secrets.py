#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from configuration import config
from modules.constants import KubernetesBrokerHttpStatus, TapComponent as TAP
from modules.markers import components, incremental
from modules.tap_logger import step
from modules.tap_object_model import KubernetesCluster, KubernetesSecret
from tests.fixtures import assertions


logged_components = (TAP.kubernetes_broker,)
pytestmark = [components.kubernetes_broker]


@pytest.fixture(scope="module")
def cluster(core_org):
    step("Check if cluster exists")
    clusters = KubernetesCluster.demiurge_api_get_list()
    cluster = next((c for c in clusters if c.name == core_org.guid), None)
    if cluster is None:
        step("Cluster does not exists for core org. Create new cluster")
        KubernetesCluster.demiurge_api_create(core_org.guid)


@incremental
@pytest.mark.skipif(not config.CONFIG["kubernetes"], reason="No point to run without kuberentes")
@pytest.mark.usefixtures("cluster")
class TestSecrets:

    def test_1_create_secret(self, core_org):
        step("Create new secret")
        self.__class__.secret = KubernetesSecret.create(org_guid=core_org.guid)
        step("Get secret and check both are the same")
        secret = KubernetesSecret.get(org_guid=core_org.guid, key_id=self.secret.key_id)
        assert self.secret == secret

    def test_2_update_secret(self, core_org):
        step("Update secret password")
        new_password = KubernetesSecret.generate_random_string()
        self.secret.update(new_password=new_password)
        step("Check password was updated")
        new_secret = KubernetesSecret.get(org_guid=core_org.guid, key_id=self.secret.key_id)
        assert new_secret.password == new_password

        step("Update secret username")
        new_username = KubernetesSecret.generate_random_string()
        self.secret.update(new_username=new_username)
        step("Check username was updated")
        new_secret = KubernetesSecret.get(org_guid=core_org.guid, key_id=self.secret.key_id)
        assert new_secret.username == new_username

    def test_3_delete_secret(self, core_org):
        step("Delete secret")
        self.secret.delete()
        step("Check the secret no longer exists")
        error_message = KubernetesBrokerHttpStatus.MSG_SECRET_NOT_FOUND.format(self.secret.key_id)
        assertions.assert_raises_http_exception(KubernetesBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, error_message,
                                                KubernetesSecret.get, org_guid=core_org.guid, key_id=self.secret.key_id)


@pytest.mark.usefixtures("cluster")
@pytest.mark.skipif(not config.CONFIG["kubernetes"], reason="No point to run without kuberentes")
class TestSecretsNegativeCases:

    def test_cannot_create_secret_with_existing_id(self, core_org):
        step("Create secret")
        secret = KubernetesSecret.create(org_guid=core_org.guid)
        step("Try to create secret with existing key_id")
        error_message = KubernetesBrokerHttpStatus.MSG_SECRET_ALREADY_EXISTS.format(secret.key_id)
        assertions.assert_raises_http_exception(KubernetesBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, error_message,
                                                KubernetesSecret.create, org_guid=core_org.guid, key_id=secret.key_id)

    def test_cannot_create_secret_with_wrong_id(self, core_org):
        step("Create secret with not-allowed id")
        key_id = "letters not allowed"
        error_message = KubernetesBrokerHttpStatus.MSG_INVALID_SECRET.format(key_id)
        assertions.assert_raises_http_exception(KubernetesBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, error_message,
                                                KubernetesSecret.create, org_guid=core_org.guid, key_id=key_id)

    def test_cannot_get_secret_with_not_existing_id(self, core_org):
        step("Try to get secret with not existing id")
        key_id = KubernetesSecret.generate_key(key_len=20)
        error_message = KubernetesBrokerHttpStatus.MSG_SECRET_NOT_FOUND.format(key_id)
        assertions.assert_raises_http_exception(KubernetesBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, error_message,
                                                KubernetesSecret.get, org_guid=core_org.guid, key_id=key_id)

    def test_cannot_update_secret_with_not_existing_id(self, core_org):
        step("Try to update secret with not existing id")
        secret = KubernetesSecret(org_guid=core_org.guid, key_id=KubernetesSecret.generate_key(key_len=20),
                                  username="test_username", password="test_password")
        error_message = KubernetesBrokerHttpStatus.MSG_SECRET_NOT_FOUND.format(secret.key_id)
        assertions.assert_raises_http_exception(KubernetesBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, error_message,
                                                secret.update)

    def test_cannot_delete_secret_with_not_existing_id(self, core_org):
        step("Try to delete secret with not existing id")
        secret = KubernetesSecret(org_guid=core_org.guid, key_id=KubernetesSecret.generate_key(key_len=20),
                                  username="test_username", password="test_password")
        error_message = KubernetesBrokerHttpStatus.MSG_SECRET_NOT_FOUND.format(secret.key_id)
        assertions.assert_raises_http_exception(KubernetesBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, error_message,
                                                secret.delete)
