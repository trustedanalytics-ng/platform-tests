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
from retry import retry

from config import jumpbox_hostname, jumpbox_key_path, jumpbox_username, kubernetes
from modules.constants import ServiceLabels, TapComponent as TAP
from modules.constants.services import ServicePlan
from modules.markers import incremental, priority
from modules.ssh_client import DirectSshClient
from modules.tap_logger import get_logger, step
from modules.tap_object_model import KubernetesCluster, KubernetesInstance, ServiceInstance, ServiceKey, ServiceType

logger = get_logger(__name__)

logged_components = (TAP.service_catalog, TAP.kubernetes_broker)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.kubernetes_broker)]


KUBECTL_DOWNLOAD_URL = "http://storage.googleapis.com/kubernetes-release/release/v1.2.0/bin/linux/amd64/kubectl"

GET_PODS_LIST_CMD = ["./kubectl", "get", "pod"]
GET_SERVICES_LIST_CMD = ["./kubectl", "get", "services"]

CLUSTER_SIZE_QUERY = "show status like 'wsrep_cluster_size';"
DB_NAME = "test_database"
CREATE_DB = "CREATE DATABASE {};".format(DB_NAME)
TABLE_NAME = "{}.students".format(DB_NAME)
CREATE_TABLE = "CREATE TABLE {} (StudentId int, LastName varchar(255));".format(TABLE_NAME)
INSERT = ["INSERT INTO {} VALUES (1, 'Kowalski');".format(TABLE_NAME),
          "INSERT INTO {} VALUES (2, 'Nowak');".format(TABLE_NAME),
          "INSERT INTO {} VALUES (3, 'Robak');".format(TABLE_NAME),
          "INSERT INTO {} VALUES (4, 'Zenonowicz');".format(TABLE_NAME)]
SELECT = "SELECT * FROM {};".format(TABLE_NAME)

CLUSTER_SIZE_RESPONSE = "wsrep_cluster_size"
ACCESS_DENIED_RESPONSE = "Access denied"
RECORD = ["1\tKowalski", "2\tNowak", "3\tRobak", "4\tZenonowicz"]


@pytest.mark.skipif(not kubernetes, reason="No point to run without Kubernetes")
@priority.medium
@incremental
class TestMySQLClusteredService:
    service_label = ServiceLabels.MYSQL_MULTINODE
    plan_name = ServicePlan.CLUSTERED

    @pytest.mark.bugs("DPNG-9701 500 Internal Server Error while successful creating organization")
    def test_0_create_mysql_clustered_service(self, class_context, test_org, test_space):
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=test_space.guid)
        self.__class__.k8s_service = next((s for s in marketplace if s.label == self.service_label), None)
        assert self.k8s_service is not None, "{} not available".format(self.service_label)
        self.__class__.instance = ServiceInstance.api_create_with_plan_name(class_context, test_org.guid,
                                                                            test_space.guid, self.service_label,
                                                                            service_plan_name=ServicePlan.CLUSTERED)
        self.instance.ensure_created()

    def test_1_get_key_for_instance(self):
        self.__class__.key = ServiceKey.api_create(self.instance.guid)
        assert "dbname" in self.key.credentials, "dbname field not found in key's credentials"
        assert "username" in self.key.credentials, "username field not found in key's credentials"
        assert "password" in self.key.credentials, "password field not found in key's credentials"

    @pytest.mark.bugs("DPNG-9520 Pending status for mysql56-clustered")
    def test_2_expose_service_instance(self, test_org, test_space):
        plan_guid = next((p["guid"] for p in self.k8s_service.service_plans if p["name"] == self.plan_name), None)
        self.__class__.k8s_instance = KubernetesInstance.from_service_instance(self.instance.guid, plan_guid,
                                                                               test_space.guid, test_org.guid)
        self.k8s_instance.ensure_running_in_cluster()
        self.k8s_instance.change_visibility(visibility=True)
        self.k8s_instance.get_info()
        assert self.k8s_instance.is_visible, "Instance is not exposed"

    def test_3_check_cluster_name_is_equal_to_org_guid(self, test_org):
        clusters = KubernetesCluster.demiurge_api_get_list()
        self.__class__.cluster = next((cluster for cluster in clusters if cluster.name == test_org.guid), None)
        assert self.cluster is not None, "Cluster was not found on demiurge list"

    def test_4_get_legacy_address(self, ssh_client):
        user_credentials = "{}:{}".format(self.cluster.username, self.cluster.password)
        endpoint_address = self.cluster.api_server + "/api/v1/nodes"
        cmd = ["curl", "-k", "--basic", "--user", user_credentials, endpoint_address]
        response, _ = ssh_client.exec_command(cmd)
        assert response
        self.__class__.legacy_address = json.loads(response)["items"][0]["status"]["addresses"][0]["address"]
        assert self.legacy_address

    @pytest.mark.usefixtures("ensure_kubectl_exists")
    def test_5_get_k8s_pods_info(self, ssh_client, cluster_prefix):
        response, _ = ssh_client.exec_command(cluster_prefix + GET_PODS_LIST_CMD)
        assert response
        self.__class__.pods_info = parse_pod_response(response)
        assert len(self.pods_info) == 3
        assert "-node1-" in self.pods_info[0]['NAME']
        assert "-node2-" in self.pods_info[1]['NAME']
        assert "-node3-" in self.pods_info[2]['NAME']
        assert self.pods_info[0]['STATUS'] == "Running"
        assert self.pods_info[1]['STATUS'] == "Running"
        assert self.pods_info[2]['STATUS'] == "Running"

    def test_6_get_k8s_services_info(self, ssh_client, cluster_prefix):
        response, _ = ssh_client.exec_command(cluster_prefix + GET_SERVICES_LIST_CMD)
        self.__class__.services_info = parse_service_response(response)
        assert response
        assert self.services_info[0]["NAME"] == "kubernetes"
        assert self.services_info[1]["NAME"].endswith("-node1")
        assert self.services_info[2]["NAME"].endswith("-node2")
        assert self.services_info[3]["NAME"].endswith("-node3")

    def test_7_should_login_to_db(self, mysql_clients):
        client = mysql_clients[0]
        response, _ = client.exec_query(CLUSTER_SIZE_QUERY)
        assert CLUSTER_SIZE_RESPONSE in response

    def test_8_should_not_login_with_corrupted_credentials(self, mysql_client_invalid_user):
        response, _ = mysql_client_invalid_user.exec_query(CLUSTER_SIZE_QUERY)
        assert CLUSTER_SIZE_RESPONSE not in response
        assert ACCESS_DENIED_RESPONSE in response

    def test_9_should_not_login_with_empty_credentials(self, mysql_client_empty_user):
        response, _ = mysql_client_empty_user.exec_query(CLUSTER_SIZE_QUERY)
        assert CLUSTER_SIZE_RESPONSE not in response
        assert ACCESS_DENIED_RESPONSE in response

    def test_10_create_db_and_insert_data(self, mysql_client_from_kubectl):
        mysql_client_from_kubectl.exec_query(CREATE_DB)
        mysql_client_from_kubectl.exec_query(CREATE_TABLE)
        mysql_client_from_kubectl.exec_query(INSERT[0])
        response, _ = mysql_client_from_kubectl.exec_query(SELECT)
        assert RECORD[0] in response

    def test_11_db_should_be_created_on_all_nodes(self, mysql_clients):
        for node_nb, client in enumerate(mysql_clients, start=1):
            response, _ = client.exec_query(SELECT)
            assert RECORD[0] in response, "Record not exists on {} node".format(node_nb)

    def test_12_deleted_pod_should_be_recreated(self, ssh_client, cluster_prefix):
        old_pod_name = self.pods_info[2]["NAME"]
        cmd = ["./kubectl", "delete", "pod", old_pod_name]
        ssh_client.exec_command(cluster_prefix + cmd)

        def get_pods_info():
            response, _ = ssh_client.exec_command(cluster_prefix + GET_PODS_LIST_CMD)
            return parse_pod_response(response)

        assert_old_pod_is_deleted(old_pod_name, get_pods_info)
        assert_new_pod_is_created(old_pod_name, get_pods_info)
        self.__class__.pods_info = get_pods_info()

    def test_13_nodes_should_be_synchronized(self, mysql_clients):
        for node_nb, client in enumerate(mysql_clients, start=1):
            response, _ = client.exec_query(SELECT)
            assert "\r\n".join(RECORD[:node_nb]) in response

            client.exec_query(INSERT[node_nb])

            response, _ = client.exec_query(SELECT)
            assert "\r\n".join(RECORD[:node_nb+1]) in response

    @pytest.fixture(scope="class", autouse=True)
    def cleanup(self, request):
        def fin():
            step("Cleanup")
            if hasattr(self, "key"):
                self.key.cleanup()
            if hasattr(self, "k8s_instance"):
                self.k8s_instance.delete()

        request.addfinalizer(fin)

    @pytest.fixture
    def cluster_prefix(self):
        user_at_host = "core@{}".format(self.legacy_address)
        return ["sudo", "ssh", "-tt", "-o StrictHostKeyChecking=no", user_at_host]

    @staticmethod
    @pytest.fixture
    def ensure_kubectl_exists(ssh_client, cluster_prefix):
        get_kubectl_cmd = ["wget", KUBECTL_DOWNLOAD_URL]
        _, err = ssh_client.exec_command(cluster_prefix + get_kubectl_cmd)
        if err:
            logger.warning("Stderr while downloading kubectl: {}".format(err))
        set_permission_cmd = ["chmod", "+x", "kubectl"]
        _, err = ssh_client.exec_command(cluster_prefix + set_permission_cmd)
        if err:
            logger.warning("Stderr while giving permission to kubectl: {}".format(err))

    @pytest.fixture
    def mysql_clients(self, ssh_client, pod_prefix):
        self.__class__.key = ServiceKey.api_create(self.instance.guid)
        client_1 = self.mysql_client_for_node(0, ssh_client, pod_prefix)
        client_2 = self.mysql_client_for_node(1, ssh_client, pod_prefix)
        client_3 = self.mysql_client_for_node(2, ssh_client, pod_prefix)
        return client_1, client_2, client_3

    def mysql_client_for_node(self, node_nb, ssh_client, pod_prefix):
        return MysqlClient(ssh_client=ssh_client,
                           pod_prefix=pod_prefix,
                           host=self.key.credentials["nodes"][node_nb]["host"],
                           port=self.key.credentials["nodes"][node_nb]["ports"]["3306/tcp"],
                           user=self.key.credentials["username"],
                           password=self.key.credentials["password"],
                           dbname=self.key.credentials["dbname"])

    @pytest.fixture
    def mysql_client_invalid_user(self, ssh_client, pod_prefix):
        return MysqlClient(ssh_client=ssh_client,
                           pod_prefix=pod_prefix,
                           host=self.key.credentials["nodes"][0]["host"],
                           port=self.key.credentials["nodes"][0]["ports"]["3306/tcp"],
                           user="SomeUser",
                           password="SomePassword",
                           dbname=self.key.credentials["dbname"])

    @pytest.fixture
    def mysql_client_empty_user(self, ssh_client, pod_prefix):
        return MysqlClient(ssh_client=ssh_client,
                           pod_prefix=pod_prefix,
                           host=self.key.credentials["nodes"][0]["host"],
                           port=self.key.credentials["nodes"][0]["ports"]["3306/tcp"],
                           user="",
                           password="",
                           dbname=self.key.credentials["dbname"])

    @pytest.fixture
    def mysql_client_from_kubectl(self, ssh_client, pod_prefix):
        return MysqlClient(ssh_client=ssh_client,
                           pod_prefix=pod_prefix,
                           host=self.services_info[1]["CLUSTER-IP"],
                           port=self.services_info[1]["PORT(S)"][0],
                           user=self.key.credentials["username"],
                           password=self.key.credentials["password"],
                           dbname=self.key.credentials["dbname"])

    @pytest.fixture
    def pod_prefix(self, cluster_prefix):
        pod_name = self.pods_info[0]['NAME']
        return cluster_prefix + ["./kubectl", "exec", pod_name, "-it", "--"]

    @pytest.fixture
    def ssh_client(self, request):
        client = DirectSshClient(hostname=jumpbox_hostname,
                                 username=jumpbox_username,
                                 path_to_key=jumpbox_key_path)
        client.connect()
        request.addfinalizer(client.disconnect)
        return client


@retry(AssertionError, tries=20, delay=3)
def assert_old_pod_is_deleted(old_pod_name, new_pods_callable):
    old_pod = next((pod for pod in new_pods_callable() if pod["NAME"] == old_pod_name), None)
    assert old_pod is None, "Old pod is still visible (not deleted)"


@retry(AssertionError, tries=20, delay=3)
def assert_new_pod_is_created(old_pod_name, new_pods_callable):
    pod_name_prefix = "-".join(old_pod_name.split("-")[:2])
    new_pod = next(p for p in new_pods_callable() if old_pod_name != p["NAME"] and pod_name_prefix in p["NAME"])
    assert new_pod, "New pod not found"


def parse_pod_response(response):
    nodes = [node for node in response.split("\n") if node]
    labels = nodes.pop(0).split()
    key_value_list_per_node = (zip(labels, node.split()) for node in nodes)
    return [dict(key_value_list) for key_value_list in key_value_list_per_node]


def parse_service_response(response):
    services_list = parse_pod_response(response)
    for service in services_list:
        service["PORT(S)"] = service["PORT(S)"].replace("/TCP", "").split(",")
    return services_list


class CannotConnectToMySQL(Exception):
    response = ""
    err = ""

    def __init__(self, response, err):
        self.response = response
        self.err = err


class MysqlClient:
    def __init__(self, ssh_client, pod_prefix, host, port, user, password, dbname):
        self.ssh_client = ssh_client
        self.pod_prefix = pod_prefix
        self.mysql_prefix = self._mysql_prefix(host, port, user, password, dbname)

    @staticmethod
    def _mysql_prefix(host, port, user, password, dbname):
        hostname_arg = "--host={}".format(host)
        port_arg = "--port={}".format(port)
        user_arg = "--user={}".format(user)
        password_arg = "--password={}".format(password)
        return " ".join(["mysql", hostname_arg, port_arg, user_arg, password_arg, dbname, "-Bse"])

    def _mysql_cmd(self, query):
        return ["\"" + self.mysql_prefix + "\\\"" + query + "\\\"" + "\""]

    @retry(CannotConnectToMySQL, tries=30, delay=10)
    def exec_query(self, query):
        cmd = self.pod_prefix + self._mysql_cmd(query)
        response, err = self.ssh_client.exec_command(cmd)
        if "Can't connect to MySQL" in response:
            raise CannotConnectToMySQL(response, err)
        return response, err
