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
import collections
import json
import os
from datetime import datetime

import pytest
from retry import retry

import config
from modules import kerberos
from modules.constants import TapComponent as TAP
from modules.constants.project_paths import Path
from modules.constants.urls import Urls
from modules.http_calls import hue
from modules.http_client import HttpClientFactory
from modules.http_client.configuration_provider.uaa import UaaConfigurationProvider
from modules.markers import priority, incremental
from modules.ssh_client import CdhMasterClient
from modules.tap_logger import step
from modules.tap_object_model import Application
from modules.tap_object_model.flows.data_catalog import create_dataset_from_file, create_dataset_from_link
from modules.tap_object_model.hdfs_job import JobStatus
from modules.test_names import generate_test_object_name

logged_components = (TAP.data_catalog, TAP.das)


@pytest.mark.skip(reason="Not yet adjusted to new TAP")
@priority.low
@incremental
class TestSparkViaHue:
    CSV_FILE_PATH = Path._2_kilobytes_csv_file

    @staticmethod
    def get_words_count(file_path):
        result = []
        with open(file_path) as file:
            counts = collections.Counter(line.strip() for line in file)
        for word, count in counts.most_common():
            result.append(word)
            result.append(count)
        return result

    @staticmethod
    def generate_job_properties(app_hdfs_path, admin_user):
        job_properties = open(
            "{}{}".format(os.getcwd(), "/tests/test_functional/data_catalog/data/job.properties")).read()
        job_properties = job_properties.replace("user.name=", "user.name={}".format(admin_user.guid))
        job_properties = job_properties.replace("oozie.wf.application.path=",
                                                "oozie.wf.application.path={}".format(app_hdfs_path))
        return job_properties

    @staticmethod
    def generate_workflow(job_name, main_class, csv_hdfs_path, output_name):
        workflow = open("{}{}".format(os.getcwd(), "/tests/test_functional/data_catalog/data/workflow.xml")).read()
        workflow = workflow.replace("app_name", job_name)
        workflow = workflow.replace("<main-class></main-class>", "<main-class>{}</main-class>".format(main_class))
        workflow = workflow.replace("<arg>target_uri</arg>", "<arg>{}</arg>".format(csv_hdfs_path))
        workflow = workflow.replace("<arg>output_path</arg>", "<arg>{}</arg>".format(output_name))
        return workflow

    def test_0_create_transfer_and_dataset_with_csv(self, class_context, test_org, add_admin_to_test_org):
        step("Create dataset from csv link")
        _, dataset = create_dataset_from_file(context=class_context, org_guid=test_org.guid,
                                              file_path=self.CSV_FILE_PATH)
        step("Create csv hdfs path")
        self.__class__.csv_hdfs_path = dataset.target_uri.replace("hdfs://nameservice1", "")

    def test_1_create_transfer_and_dataset_from_hadoop_mapreduce_examples(self, class_context, test_org,
                                                                          add_admin_to_test_org):
        step("Create dataset from hadoop mapreduce examples jar")
        _, dataset = create_dataset_from_link(context=class_context, org_guid=test_org.guid,
                                              source=Urls.hadoop_mapreduce_examples)
        step("Create jar path")
        self.__class__.jar_path = dataset.target_uri.replace("hdfs://nameservice1", "")

    def test_2_create_java_job_design(self):
        step("Create output name")
        self.__class__.output_name = generate_test_object_name(prefix="/tmp/out_test")
        step("Create arguments for a job")
        args = "{} {}".format(self.csv_hdfs_path, self.output_name)
        step("Create job name")
        self.__class__.job_name = generate_test_object_name(prefix="java_job")
        step("Create name of job main class")
        self.__class__.main_class = "org.apache.hadoop.examples.WordCount"
        step("Create java job design in hue job designer")
        java_job_design = hue.create_java_job_design(name=self.job_name, jar_path=self.jar_path,
                                                     main_class=self.main_class, args=args,
                                                     description="hadoop-mapreduce-examples")
        assert self.job_name == java_job_design["name"], "Java job design in Hue has wrong name"

    def test_3_submit_java_job_design(self, admin_user):
        step("Create application hdfs path name")
        app_hdfs_path = generate_test_object_name(prefix="hdfs://nameservice1/user/hue/oozie/workspaces/_{}_-oozie-".
                                                  format(admin_user.guid))
        step("Create Cdh master 2 client")
        self.__class__.client = CdhMasterClient(cdh_host_name=config.cdh_master_2_hostname)
        step("Create directory to store oozie data")
        properties_path = "/tmp/{}".format(datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        step("Get oozie url")
        app_name = TAP.cdh_broker
        cdh_broker = next((app for app in Application.cf_api_get_list() if app_name == app.name), None)
        assert cdh_broker is not None, "{} not available".format(app_name)
        oozie_url = str(json.loads(cdh_broker.cf_api_env()["ENVIRONMENT_JSON"]["CREDENTIALS"])["resource_manager"]). \
            replace("8088", "11000/oozie")
        step("Prepare commands needed before job design execution")
        cmds = [
            ["mkdir", properties_path],
            ["echo", "non-kerberos"],
            ["echo", self.generate_job_properties(admin_user=admin_user, app_hdfs_path=app_hdfs_path)],
            ["cp", "{}{}".format(self.client._output_path, "/2_1"), "{}{}".format(properties_path, "/job.properties")],
            ["echo", self.generate_workflow(job_name=self.job_name, main_class=self.main_class,
                                            csv_hdfs_path=self.csv_hdfs_path, output_name=self.output_name)],
            ["cp", "{}{}".format(self.client._output_path, "/4_1"), "{}{}".format(properties_path, "/workflow.xml")],
            ["hadoop ", "fs", "-mkdir", app_hdfs_path],
            ["hadoop ", "fs", "-copyFromLocal", "{}{}".format(properties_path, "/workflow.xml"), app_hdfs_path],
        ]
        step("Check if this is kerberos environment")
        if kerberos.is_kerberos_environment():
            step("If kerberos environment: add ktinit with oauth token to commands")
            client = HttpClientFactory.get(UaaConfigurationProvider.get(config.admin_username, config.admin_password))
            cmds[1] = ["ktinit", "-t", client.auth.token]

        step("Execute commands: Create job.properties and workflow.xml files at cdh-master-2; Create hdfs directory;"
             "Copy workflow.xml to hdfs directory")
        self.client.exec_commands(
            cmds
        )
        step("Run java job design")
        submited_job = self.client.exec_commands(
            [
                ["oozie", "job", "-oozie", oozie_url, "-config",
                 "{}{}".format(properties_path, "/job.properties"), "-run"]
            ]
        )
        assert "job" in submited_job[0][0], "Job was not created"
        step("Get job workflow id")
        self.__class__.workflow_id = submited_job[0][0].strip("job: ")

    @retry(AssertionError, tries=8, delay=15)
    def test_4_ensure_job_is_completed(self):
        job_workflow = hue.get_job_workflow(workflow_id=self.workflow_id)
        step("Check job status is SUCCEEDED")
        assert job_workflow["status"] == JobStatus.SUCCEEDED.value
        step("Check job progress is 100%")
        assert job_workflow["progress"] == 100

    def test_5_check_job_output(self):
        step("Check if there is output file in /tmp folder")
        files_list = self.client.exec_commands([["hdfs", "dfs", "-ls", "/tmp"]])
        assert self.output_name in files_list[0][0], "Output file is unavailable"
        step("Check file content")
        file_content = self.client.exec_commands([["hdfs", "dfs", "-cat", "{}/*".format(self.output_name)]])
        assert all([str(i) in file_content[0][0] for i in self.get_words_count(file_path=self.CSV_FILE_PATH)]), \
            "Output is incorrect"
