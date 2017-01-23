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
from datetime import datetime
import re

from ..http_calls.platform import grafana_metrics
from modules.constants import TapEntityState
from modules.exceptions import UnexpectedResponseError
from .kubernetes_node import KubernetesNode


class Metrics(object):

    MEMORY_USAGE_NODE_METRICS_KEY = 'container_memory_cache{id="/"}'
    CPU_USAGE_NODE_METRICS_KEY = 'container_cpu_system_seconds_total{id="/"}'
    MEMORY_RATE = 1000000000  # we receive a value multipled by e+9
    CPU_RATE_FOR_GRAFANA = 100  # reduce value to percentage
    CPU_RATE_FOR_REF = 1000  # reduce received value from s to ms
    NODE = 3  # number of nodes

    def __init__(self, apps=None, apps_running=None, apps_down=None, users_org=None, users_platform=None, orgs=None,
                 service_usage=None, services=None, service_instances=None, memory_usage_org=None,
                 memory_usage_platform=None, cpu_usage_org=None, cpu_usage_platform=None, datasets=None):
        self.apps = apps
        self.apps_running = apps_running
        self.apps_down = apps_down
        self.apps_down = apps_down
        self.users_org = users_org
        self.users_platform = users_platform
        self.orgs = orgs
        self.service_usage = service_usage
        self.services = services
        self.service_instances = service_instances
        self.memory_usage_org = memory_usage_org
        self.memory_usage_platform = memory_usage_platform
        self.cpu_usage_org = cpu_usage_org
        self.cpu_usage_platform = cpu_usage_platform
        self.datasets = datasets
        self.timestamp = datetime.now()

    def __repr__(self):
        return self.__class__.__name__

    @classmethod
    def from_reference(cls, org_guid):
        from modules.tap_object_model import Application, User, Organization, ServiceOffering, ServiceInstance, DataSet
        metrics = []
        app_down_states = [TapEntityState.FAILURE, TapEntityState.STOPPED]

        apps = Application.get_list()
        apps_count = len(apps)
        apps_running_count = len([app for app in apps if app.state == TapEntityState.RUNNING])
        apps_down_count = len([app for app in apps if app.state in app_down_states])
        user_count = len(User.get_all_users(org_guid))
        orgs_count = len(Organization.get_list())
        services_count = len(ServiceOffering.get_list())
        services_inst = len([instance for instance in ServiceInstance.get_list()
                             if instance.state == TapEntityState.RUNNING])

        nodes = KubernetesNode.get_list()
        for node in nodes:
            metrics.append(node.get_metrics())

        cpu_usage_org = cls.parse_cpu(metrics) / (cls.CPU_RATE_FOR_REF * cls.NODE)
        cpu_usage_platform = cls.parse_cpu(metrics) / (cls.CPU_RATE_FOR_REF * cls.NODE)
        memory_usage_org = cls.parse_memory(metrics)
        memory_usage_platform = cls.parse_memory(metrics)

        datasets = DataSet.api_get_list(org_guid_list=[org_guid])

        return cls(apps=apps_count, apps_running=apps_running_count, apps_down=apps_down_count, users_org=user_count,
                   users_platform=user_count, orgs=orgs_count, services=services_count, service_instances=services_inst,
                   service_usage=services_inst, cpu_usage_org=cpu_usage_org, memory_usage_org=memory_usage_org,
                   cpu_usage_platform=cpu_usage_platform, memory_usage_platform=memory_usage_platform,
                   datasets=datasets)

    @classmethod
    def parse_cpu(cls, metrics):
        cpu_summary = 0.0
        for node in metrics:
            for line in node.split("\n"):
                if cls.CPU_USAGE_NODE_METRICS_KEY in line:
                    memory_metrics = re.search(r'\d+\.*\d*', line)
                    assert memory_metrics is not None
                    cpu_summary += float(memory_metrics.group(0))

        return cpu_summary

    @classmethod
    def parse_memory(cls, metrics):
        memory_summary = 0.0
        for node in metrics:
            for line in node.split("\n"):
                if cls.MEMORY_USAGE_NODE_METRICS_KEY in line:
                    memory_metrics = re.search(r'\d+\.*\d*', line)
                    assert memory_metrics is not None
                    memory_summary += float(memory_metrics.group(0))

        return memory_summary

    @classmethod
    def from_grafana(cls, metrics_level=None, client=None):
        metrics_values = {}
        metrics = {"apps_running": "1", "apps_down": "2", "users_org": "3", "service_usage": "4",
                   "memory_usage_org": "5", "cpu_usage_org": "6", "datasets": "7"}
        if metrics_level == "platform":
            metrics = {"apps": "1", "services": "2", "service_instances": "3", "orgs": "4", "users_platform": "5",
                       "memory_usage_platform": "7", "cpu_usage_platform": "8"}
        for panel_value in metrics:
            try:
                tmp = grafana_metrics.api_get_metric(client, panel_id=metrics[panel_value], metrics_level=metrics_level)
                metrics_values[panel_value] = float(tmp["data"]["result"][0]["values"][0][1])
            except IndexError:
                metrics_values[panel_value] = float('nan')  # when prometheus and grafana dont have enough data
            except UnexpectedResponseError as e:
                if "bad data" in e.error_message:
                    metrics_values[panel_value] = float('nan')  # in case someone ruins grafana query
                else:
                    raise
            continue

        if metrics_level == "platform":
            return cls(apps=metrics_values["apps"], services=metrics_values["services"],
                       service_instances=metrics_values["service_instances"],
                       orgs=metrics_values["orgs"], users_platform=metrics_values["users_platform"],
                       memory_usage_platform=(metrics_values["memory_usage_platform"] / cls.MEMORY_RATE),
                       cpu_usage_platform=(metrics_values["cpu_usage_platform"] * cls.CPU_RATE_FOR_GRAFANA))
        else:
            return cls(apps_running=metrics_values["apps_running"],
                       apps_down=metrics_values["apps_down"],
                       users_org=metrics_values["users_org"], service_usage=metrics_values["service_usage"],
                       memory_usage_org=(metrics_values["memory_usage_org"] / cls.MEMORY_RATE),
                       cpu_usage_org=(metrics_values["cpu_usage_org"] * cls.CPU_RATE_FOR_GRAFANA),
                       datasets=metrics_values["datasets"])
