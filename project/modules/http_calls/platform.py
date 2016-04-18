#
# Copyright (c) 2015-2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License";
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
import os

from ..exceptions import YouMustBeJokingException
from ..api_client import PlatformApiClient
from ..http_calls import cloud_foundry as cf



# =============================================== app-launcher-helper ================================================ #


def api_get_atk_instances(org_guid, client=None):
    """GET /rest/orgs/{organization_guid}/atkinstances"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs/{}/atkinstances".format(org_guid),
                          log_msg="PLATFORM: get list of atk instances")


# ======================================================== das ======================================================= #


def api_get_transfers(org_guids=None, query="", filters=(), size=12, time_from=0, client=None):
    """GET /rest/das/requests"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {
        "query": query,
        "filters": list(filters),
        "size": size,
        "from": time_from
    }
    if org_guids is not None:
        query_params["orgs"] = ",".join(org_guids)
    return client.request("GET", "rest/das/requests", params=query_params,
                          log_msg="PLATFORM: get filtered transfer list")


def api_create_transfer(category=None, is_public=None, org_guid=None, source=None, title=None, client=None):
    """POST /rest/das/requests"""
    body_keys = ["category", "publicRequest", "orgUUID", "source", "title"]
    values = [category, is_public, org_guid, source, title]
    body = {key: val for key, val in zip(body_keys, values) if val is not None}
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/das/requests", body=body, log_msg="PLATFORM: create a transfer")


def api_create_transfer_by_file_upload(org_guid, source, category=None, is_public=None, title=None, client=None):
    """POST /rest/upload/{org_id}"""
    body_keys = ["category", "publicRequest", "orgUUID", "title"]
    values = [category, is_public, org_guid, title]
    data = {key: val for key, val in zip(body_keys, values) if val is not None}
    _, file_name = os.path.split(source)
    files = {"file": (file_name, open(source, "rb"), "application/vnd.ms-excel")}
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/upload/{}".format(org_guid), data=data, log_msg="PLATFORM: create a transfer",
                          files=files)


def api_get_transfer(request_id, client=None):
    """GET /rest/das/requests/{request_id}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/das/requests/{}".format(request_id), log_msg="PLATFORM: get transfer")


def api_delete_transfer(request_id, client=None):
    """DELETE /rest/das/requests/{request_id}"""
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/das/requests/{}".format(request_id), log_msg="PLATFORM: delete transfer")


# =================================================== data-catalog =================================================== #


def api_get_datasets(org_guid_list=None, query="", filters=(), size=12, time_from=0, only_private=False,
                     only_public=False, client=None):
    """GET /rest/datasets"""
    query_params = {
        "query": json.dumps({"query": query, "filters": list(filters), "size": size, "from": time_from})
    }
    if org_guid_list is not None:
        query_params["orgs"] = ",".join(org_guid_list)
    if only_private:
        query_params["onlyPrivate"] = only_private
    if only_public:
        query_params["onlyPublic"] = only_public
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/datasets", params=query_params, log_msg="PLATFORM: get filtered list of data sets")


def api_get_dataset(entry_id, client=None):
    """GET /rest/datasets/{entry_id}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/datasets/{}".format(entry_id), log_msg="PLATFORM: get data set")


def api_delete_dataset(entry_id, client=None):
    """DELETE /rest/datasets/{entry_id}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/datasets/{}".format(entry_id), log_msg="PLATFORM: delete data set")


def api_update_dataset(entry_id, creation_time=None, target_uri=None, category=None, format=None,
                       record_count=None, is_public=None, org_guid=None, source_uri=None, size=None, data_sample=None,
                       title=None, client=None):
    """POST /rest/datasets/{entry_id}"""
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/datasets/{}".format(entry_id), body=body, log_msg="PLATFORM: update data set")


def api_put_dataset_in_index(entry_id, creation_time=None, target_uri=None, category=None, format=None,
                             record_count=None, is_public=None, org_guid=None, source_uri=None, size=None,
                             data_sample=None, title=None, client=None):
    """PUT /rest/datasets/{entry_id}"""
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    client = client or PlatformApiClient.get_admin_client()
    return client.request("PUT", "rest/datasets/{}".format(entry_id), body=body, log_msg="PLATFORM: put data set in index")


def api_get_dataset_count(org_guid_list, only_private, only_public, client=None):
    """GET /rest/datasets/count"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/datasets/count", log_msg="PLATFORM: get filtered data set count")


# ================================================== file-server ===================================================== #


def api_get_atk_client_file_name(client=None):
    """GET /files/atkclient"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "files/atkclient", log_msg="PLATFORM: get atk client file name")
    return response["file"]


def api_get_file(source_file_name, target_file_path, client=None):
    """GET /files/{file_name}"""
    client = client or PlatformApiClient.get_admin_client()
    client.download_file(endpoint="files/{}".format(source_file_name), target_file_path=target_file_path)


# ============================================= hive / dataset-publisher ============================================= #


def api_publish_dataset(category, creation_time, data_sample, format, is_public,
                        org_guid, record_count, size, source_uri, target_uri, title, client=None):
    """POST /rest/tables"""
    client = client or PlatformApiClient.get_admin_client()
    body = {"category": category, "creationTime": creation_time, "dataSample": data_sample, "format": format,
            "isPublic": is_public, "orgUUID": org_guid, "recordCount": record_count, "size": size,
            "sourceUri": source_uri, "targetUri": target_uri, "title": title}
    return client.request("POST", "rest/tables", body=body, log_msg="PLATFORM: publish dataset in hive")


# ============================================== latest-events-service =============================================== #


def api_get_latest_events(org_guid=None, client=None):
    """GET /rest/les/events"""
    client = client or PlatformApiClient.get_admin_client()
    params = {}
    if org_guid is not None:
        params = {"org": org_guid}
    return client.request("GET", "rest/les/events", params=params, log_msg="PLATFORM: get latest events")


# ================================================= metrics-provider ================================================= #


def api_get_org_metrics(org_guid, client=None):
    """GET /rest/orgs/{org_guid}/metrics"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs/{}/metrics".format(org_guid), log_msg="PLATFORM: get metrics")

# ================================================= platform-operations=============================================== #


def api_get_platform_operations(client=None):
    """GET /rest/platform/summary"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/platform/summary", log_msg="PLATFORM/OPERATIONS: metrics")


def api_refresh_platform_operations(client=None):
    """POST /rest/platform/summary/refresh_cache"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/platform/summary/refresh_cache", log_msg="PLATFORM/OPERATIONS: refresh")


# ================================================= platform-context ================================================= #


def api_get_external_tools(client=None):
    """GET /rest/platform_context"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/platform_context", log_msg="PLATFORM: get external tool info")


# ================================================= service-catalog ================================================== #


def api_get_marketplace_services(space_guid, client=None):
    """GET /rest/services"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/services", params={"space": space_guid},
                          log_msg="PLATFORM: get marketplace service list")


def api_get_service(service_guid, client=None):
    """GET /rest/service/{service_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/service/{}".format(service_guid), log_msg="PLATFORM: get service")


def api_get_service_instances(space_guid=None, service_guid=None, client=None):
    """GET /rest/service_instances"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {}
    if space_guid is not None:
        query_params["space"] = space_guid
    if service_guid is not None:
        query_params["broker"] = service_guid
    return client.request("GET", "rest/service_instances", params=query_params,
                          log_msg="PLATFORM: get service instance list")


def api_create_service_instance(name, service_plan_guid, org_guid, space_guid, params=None, client=None):
    """POST /rest/service_instances"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "name": name,
        "organization_guid": org_guid,
        "service_plan_guid": service_plan_guid,
        "space_guid": space_guid,
        "parameters": {"name": name}
    }
    if params is not None:
        body["parameters"].update(params)
    return client.request("POST", "rest/service_instances", body=body, log_msg="PLATFORM: create service instance")


def api_delete_service_instance(service_instance_guid, client):
    """DELETE /rest/service_instances/{service_instance_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/service_instances/{}".format(service_instance_guid),
                          log_msg="PLATFORM: delete service instance")


def api_get_service_plans(service_type_label, client):
    """GET /rest/services/{service_type_label}/service_plans"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/services/{}/service_plans".format(service_type_label),
                          log_msg="PLATFORM: get service plans")


def api_get_service_instances_summary(space_guid=None, service_keys=True, client=None):
    """GET /rest/service_instances/summary"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {}
    if space_guid:
        query_params["space"] = space_guid
    if service_keys:
        query_params["service_keys"] = service_keys
    return client.request("GET", "rest/service_instances/summary", params=query_params,
                          log_msg="PLATFORM: get service instances summary")

# --------------------------------------------------- Service Keys --------------------------------------------------- #


def api_create_service_key(name, service_instance_guid, client=None):
    """POST /rest/service_keys"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "name": name,
        "service_instance_guid": service_instance_guid,
    }
    return client.request("POST", "rest/service_keys", body=body, log_msg="PLATFORM: create service key")


def api_delete_service_key(service_key_guid, client):
    """DELETE /rest/service_keys/{service_key_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/service_keys/{}".format(service_key_guid),
                          log_msg="PLATFORM: delete service instance key")

def api_create_service_key(service_instance_guid, service_key_name, client=None):
    """POST /rest/service_keys"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "name": service_key_name,
        "service_instance_guid": service_instance_guid
    }
    return client.request(method="POST", endpoint="rest/service_keys", body=body,
                          log_msg="Platform: create service key")


def api_delete_service_key(service_key_guid, client=None):
    """DELETE /rest/service_keys/{service_key_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request(method="DELETE", endpoint="rest/service_keys/{}".format(service_key_guid),
                          log_msg="Platform: delete service key")

# --------------------------------------------------- Applications --------------------------------------------------- #


def api_get_filtered_applications(space, service_label=None, client=None):
    """GET /rest/apps"""
    client = client or PlatformApiClient.get_admin_client()
    query_params = {"space": space}
    if service_label is not None:
        query_params["service_label"] = service_label
    return client.request("GET", "rest/apps", params=query_params, log_msg="PLATFORM: get application list")


def api_get_app_summary(app_guid, client=None):
    """GET /rest/apps/{app_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/apps/{}".format(app_guid), log_msg="PLATFORM: get application summary")


def api_delete_app(app_guid, cascade=True, client=None):
    """DELETE /rest/apps/{app_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/apps/{}".format(app_guid), log_msg="PLATFORM: delete application")


def api_get_app_orphan_services(app_guid, client=None):
    """GET /rest/apps/{app_guid}/orphan_services"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/apps/{}/orphan_services".format(app_guid), log_msg="PLATFORM: get app orphan services")


def api_change_app_status(app_guid, status, client=None):
    """POST /rest/apps/{app_guid}/status"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/apps/{}/status".format(app_guid), body={"state": status},
                          log_msg="PLATFORM: restage app")


def api_get_app_bindings(app_guid, client=None):
    """GET /rest/apps/{app_guid}/service_bindings"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/apps/{}/service_bindings".format(app_guid), log_msg="PLATFORM: get app bindings")
    return response["resources"]


def api_create_service_binding(app_guid, service_instance_guid, client=None):
    """POST /rest/apps/{app_guid}/service_bindings"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "apps/{}/service_bindings".format(app_guid),
                          body={"rest/service_instance_guid": service_instance_guid},
                          log_msg="PLATFORM: Create binding for app and service")


def api_delete_service_binding(binding_guid, client=None):
    """DELETE /rest/service_bindings/{binding_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/service_bindings/{}".format(binding_guid), log_msg="PLATFORM: delete binding")


def api_create_scoring_engine(atk_name, instance_name, space_guid, service_plan_guid, client=None):
    """POST /rest/orgs/atk/scoring-engine"""
    log_msg="PLATFORM: create scoring engine for atk"
    client = client or PlatformApiClient.get_admin_client()
    raise NotImplementedError("Please implement this method if you need it")


# ================================================= service-exposer ================================================== #


def api_tools_service_instances(service_label, space_guid, org_guid=None, client=None):
    """GET /rest/tools/service_instances"""
    client = client or PlatformApiClient.get_admin_client()
    params = {
        "service": service_label,
        "space": space_guid
    }
    if org_guid is not None:
        params.update({"org": org_guid})
    return client.request("GET", "rest/tools/service_instances", params=params,
                          log_msg="PLATFORM: get tools for service instance")


# ================================================= user-management ================================================== #


def api_get_organizations(client=None):
    """GET /rest/orgs"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs", log_msg="PLATFORM: get org list")


def api_create_organization(name, client=None):
    """POST /rest/orgs"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/orgs", body={"name": name}, log_msg="PLATFORM: create an org")
    return response.strip('"')  # guid is returned together with quotation marks


def api_delete_organization(org_guid, client=None):
    """DELETE /rest/orgs/{organization_guid}"""
    ref_org_guid, _ = cf.cf_get_ref_org_and_space_guids()
    if org_guid == ref_org_guid:
        raise YouMustBeJokingException("You're trying to delete the reference org")
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/orgs/{}".format(org_guid), log_msg="PLATFORM: delete org")


def api_rename_organization(org_guid, new_name, client=None):
    """PUT /rest/orgs/{organization_guid}/name"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("PUT", "rest/orgs/{}/name".format(org_guid), body={"name": new_name},
                          log_msg="PLATFORM: rename org")


def api_add_organization_user(org_guid, username, roles=(), client=None):
    """POST /rest/orgs/{organization_guid}/users"""
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": list(roles)
    }
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/orgs/{}/users".format(org_guid), body=body, log_msg="PLATFORM: add user to org")


def api_get_organization_users(org_guid, client=None):
    """GET /rest/orgs/{organization_guid}/users"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs/{}/users".format(org_guid), log_msg="PLATFORM: get list of users in org")


def api_delete_organization_user(org_guid, user_guid, client=None):
    """DELETE /rest/orgs/{organization_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/orgs/{}/users/{}".format(org_guid, user_guid),
                          log_msg="PLATFORM: delete user from org")


def api_update_org_user_roles(org_guid, user_guid, new_roles=None, client=None):
    """POST /rest/orgs/{organization_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    body = {}
    if new_roles is not None:
        body["roles"] = list(new_roles)
    return client.request("POST", "rest/orgs/{}/users/{}".format(org_guid, user_guid), body=body,
                          log_msg="PLATFORM: update user roles in org")


def api_add_space_user(org_guid, space_guid, username, roles=(), client=None):
    """POST /rest/spaces/{space_guid}/users"""
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": list(roles)
    }
    return client.request("POST", "rest/spaces/{}/users".format(space_guid), body=body,
                          log_msg="PLATFORM: Add user to space")


def api_get_space_users(space_guid, client=None):
    """GET /rest/spaces/{space_guid}/users"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/spaces/{}/users".format(space_guid), log_msg="PLATFORM: get space users")


def api_delete_space_user(space_guid, user_guid, client=None):
    """DELETE /rest/spaces/{space_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("DELETE", "rest/spaces/{}/users/{}".format(space_guid, user_guid),
                          log_msg="PLATFORM: delete user from space")


def api_update_space_user_roles(space_guid, user_guid, new_roles=None, client=None):
    """POST /rest/spaces/{space_guid}/users/{user_guid}"""
    client = client or PlatformApiClient.get_admin_client()
    body = {}
    if new_roles is not None:
        body["roles"] = list(new_roles)
    return client.request("POST", "rest/spaces/{}/users/{}".format(space_guid, user_guid), body=body,
                          log_msg="PLATFORM: update user roles in space")


def api_get_invitations(client=None):
    """GET /rest/invitations"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/invitations", log_msg="PLATFORM: get list of all invitations")


def api_invite_user(email, client=None):
    """POST /rest/invitations"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("POST", "rest/invitations", body={"email": email}, log_msg="PLATFORM: invite new platform user")


def api_delete_invitation(email, client=None):
    """DELETE /rest/invitations/{invitation}"""
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/invitations/{}".format(email), log_msg="PLATFORM: delete invitation")


def api_resend_invitation(email, client=None):
    """POST /rest/invitations/{invitation}/resend"""
    client = client or PlatformApiClient.get_admin_client()
    client.request("POST", "rest/invitations/{}/resend".format(email), log_msg="PLATFORM: resend invitation")


def api_register_new_user(code, password=None, org_name=None, client=None):
    """POST /rest/registrations"""
    msg = "PLATFORM: register as a new user"
    if org_name is not None:
        msg += " with new organization"
    client = client or PlatformApiClient.get_admin_client()
    body = {}
    if org_name is not None:
        body["org"] = org_name
    if password is not None:
        body["password"] = password
    return client.request("POST", "rest/registrations", params={"code": code}, body=body, log_msg=msg)


def api_get_spaces_in_org(org_guid, client=None):
    """GET /rest/orgs/{org}/spaces"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/orgs/{}/spaces".format(org_guid), log_msg="PLATFORM: get list of spaces in org")


def api_get_spaces(client=None):
    """GET /rest/spaces"""
    client = client or PlatformApiClient.get_admin_client()
    return client.request("GET", "rest/spaces", log_msg="PLATFORM: get list of all spaces")


def api_create_space(org_guid, name, client=None):
    """POST /rest/spaces"""
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/spaces", body={"name": name, "org_guid": org_guid},
                              log_msg="PLATFORM: create a space")
    if response == "":
        raise AssertionError("Response to POST /rest/spaces did not return space guid.")
    return response


def api_delete_space(space_guid, client=None):
    """DELETE /rest/spaces/{space}"""
    _, ref_space_guid = cf.cf_get_ref_org_and_space_guids()
    if space_guid == ref_space_guid:
        raise YouMustBeJokingException("You're trying to delete the reference space")
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/spaces/{}".format(space_guid), log_msg="PLATFORM: delete space")


# ================================================= App Development ================================================== #


def api_get_app_development_page(client=None):
    """GET /app/tools/tools.html"""
    return client.request("GET", "app/tools/tools.html", log_msg="PLATFORM: get app development tools page")


# ================================================= Job Scheduler ================================================== #


def api_get_jobs_list(org_guid, amount, unit, client=None):
    """GET /rest/v1/oozie/jobs/workflow"""
    client = client or PlatformApiClient.get_admin_client()
    params = {
        "amount": amount,
        "org": org_guid,
        "unit": unit
    }
    return client.request("GET", "rest/v1/oozie/jobs/workflow", params=params)

def api_create_job(org_guid, name, start=None, end=None, amount=None, unit=None, zone_id=None, check_column=None,
                   import_mode=None, jdbc_uri=None, last_value=None, password=None, table=None, target_dir=None,
                   username=None, client=None):
    """POST /rest/v1/oozie/schedule_job/coordinated"""
    client = client or PlatformApiClient.get_admin_client()
    params = {"org": org_guid}
    frequency = {"amount": amount, "unit": unit}
    body_schedule_keys = ["start", "end", "frequency", "zoneId"]
    body_schedule_values = [start, end, frequency, zone_id]
    body_schedule = {key: val for key, val in zip(body_schedule_keys, body_schedule_values) if val is not None}
    body_sqoop_keys = ["checkColumn", "importMode", "jdbcUri", "lastValue", "password", "table", "targetDir", "username"]
    body_sqoop_values = [check_column, import_mode, jdbc_uri, last_value, password, table, target_dir, username]
    body_sqoop = {key: val for key, val in zip(body_sqoop_keys, body_sqoop_values) if val is not None}
    body = {"name": name, "schedule": body_schedule, "sqoopImport": body_sqoop}
    return client.request("POST", "rest/v1/oozie/schedule_job/coordinated", params=params, body=body)

def api_get_job_details(org_guid, job_id, client=None):
    """GET /rest/v1/oozie/jobs/workflow/{id}"""
    client = client or PlatformApiClient.get_admin_client()
    params = {"org": org_guid}
    return client.request("GET", "rest/v1/oozie/jobs/workflow/{}".format(job_id), params=params)
