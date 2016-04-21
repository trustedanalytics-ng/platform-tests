#!/bin/sh
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

# usage:
# add-test-admin <environment, e.g. daily.gotapaas.com> <cf admin pass> <org=seedorg> <space=seedspace> <password>

DOMAIN=$1
CF_ADMIN_PASS=$2
ORG_NAME=${3:-seedorg}
SPACE_NAME=${4:-seedspace}
USERNAME=trusted.analytics.tester@gmail.com
PASSWORD=$5


cf api api.$DOMAIN --skip-ssl-validation
cf auth admin $CF_ADMIN_PASS
cf target -o $ORG_NAME -s $SPACE_NAME

cf create-user $USERNAME $PASSWORD
cf set-org-role $USERNAME $ORG_NAME OrgManager
cf set-org-role $USERNAME $ORG_NAME OrgAuditor
cf set-org-role $USERNAME $ORG_NAME BillingManager
cf set-space-role $USERNAME $ORG_NAME $SPACE_NAME SpaceManager
cf set-space-role $USERNAME $ORG_NAME $SPACE_NAME SpaceDeveloper
cf set-space-role $USERNAME $ORG_NAME $SPACE_NAME SpaceAuditor

uaac target uaa.$DOMAIN --skip-ssl-validation
ADMIN_SECRET=`cf env user-management | grep -P -o '(?<=clientSecret\"\:\s\").*(?=\")'`
uaac token client get admin -s $ADMIN_SECRET

uaac member add cloud_controller.read $USERNAME
uaac member add cloud_controller.write $USERNAME
uaac member add cloud_controller.admin $USERNAME
uaac member add uaa.admin $USERNAME
uaac member add console.admin $USERNAME
uaac member add scim.read $USERNAME
uaac member add scim.write $USERNAME
