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

import config
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory


def get_logged_client(username=None, password=None):
    console_client = HttpClientFactory.get(ConsoleConfigurationProvider.get(username, password))
    client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=config.hue_url))
    client.session = console_client.session
    client.request(method=HttpMethod.GET, path="", msg="login")
    return client


def get_databases(client=None):
    """GET metastore/databases"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="metastore/databases",
        params={"format": "json"},
        msg="HUE: get list of databases"
    )


def get_tables(database_name, client=None):
    """GET metastore/tables/{database_name}"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="metastore/tables/{}".format(database_name),
        params={"format": "json"},
        msg="HUE: get tables"
    )


def get_table(database_name, table_name, client=None):
    """GET beeswax/api/table/{}/{}/sample"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="beeswax/api/table/{}/{}/sample".format(database_name, table_name),
        msg="HUE: get table"
    )


def get_table_metadata(database_name, table_name, client=None):
    """GET metastore/table/{database_name}/{table_name}/metadata"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="metastore/table/{}/{}/metadata".format(database_name, table_name),
        params={"format": "json"},
        msg="HUE: get table metadata"
    )


def get_file_browser(client=None):
    """GET filebrowser"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="filebrowser",
        params={"format": "json"},
        msg="HUE: file browser"
    )


def get_job_browser(client=None):
    """GET jobbrowser"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="jobbrowser",
        params={"format": "json"},
        msg="HUE: get job browser"
    )


def create_java_job_design(name, jar_path, main_class, args="", description="", client=None):
    """POST jobsub/designs/java/new"""
    if client is None:
        client = get_logged_client()
    files = "node_type=java&files=[]&name={}&jar_path={}&job_properties=[]&prepares=[]&archives=[]&main_class={}" \
            "&args={}&description={}&".format(name, jar_path, main_class, args, description)

    return client.request(
        method=HttpMethod.POST,
        path="jobsub/designs/java/new",
        files={(files, "")},
        headers=_get_headers(client, True),
        msg="HUE: create java job design"
    )


def get_job_workflow(workflow_id, client=None):
    """GET oozie/list_oozie_workflow/{workflow_id}/"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="oozie/list_oozie_workflow/{}/".format(workflow_id),
        headers=_get_headers(client),
        params={"format": "json"},
        msg="HUE: get job workflow"
    )


def query_execute(database, query, client=None):
    """POST beeswax/api/query/execute/1"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.POST,
        path="beeswax/api/query/execute/1",
        data={
            "query-query": query,
            "query-database": database,
            "settings-next_form_id": 0,
            "file_resources-next_form_id": 0,
            "functions-next_form_id": 0,
            "query-email_notify": False,
            "query-is_parameterized": True
        },
        msg="HUE: query execute",
        headers=_get_headers(client, True)
    )


def query_watch(id, client=None):
    """POST beeswax/api/watch/json"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.POST,
        path="beeswax/api/watch/json/{}".format(id),
        msg="HUE: query watch",
        headers=_get_headers(client, True)
    )


def query_result(id, client):
    """POST beeswax/results"""
    if client is None:
        client = get_logged_client()
    return client.request(
        method=HttpMethod.GET,
        path="beeswax/results/{}/0".format(id),
        msg="HUE: query watch",
        data={"format": "json"}
    )


def _get_headers(client, referer=False):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-CSRFToken": client.cookies.get('csrftoken'),
        "X-Requested-With": "XMLHttpRequest",
    }
    if referer:
        headers["Referer"] = "{}/beeswax/execute/design/".format(client.url)
    return headers
