#!/bin/sh
#Copyright (c) 2016 Intel Corporation
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
# add-test-admin <environment, e.g. xx.tap.sclab.intel.com> <uaa client pass> <username> <password>

DOMAIN=$1
ADMIN_SECRET=$2
USERNAME=$3
PASSWORD=$4
EMAIL=$USERNAME@example.com

uaac target http://uaa.$DOMAIN --skip-ssl-validation
uaac token client get admin -s $ADMIN_SECRET
uaac user add $USERNAME --email $EMAIL -p $PASSWORD
uaac member add uaa.admin $USERNAME
uaac member add tap.admin $USERNAME