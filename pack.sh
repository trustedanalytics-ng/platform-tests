#!/bin/bash
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

# Builds an artifact that can be used in offline deployment of the application.

set -e
VENDOR=vendor/
SECRETS_PATH=./project/configuration/secrets/
REQUIREMENTS_PATH=./requirements.txt
ZIPPED_ITEMS="deploy/ project/ SMOKE_TESTS_README.md build_info.ini manifest.yml requirements.txt runtime.txt"
DELETED_ITEMS="project/modules/remote_logger project/modules/cloudera_client.py project/modules/hdfs.py project/modules/hive.py project/modules/kerberos.py project/modules/ssh_client.py"

# prepare dependencies
if [ -d $VENDOR ]; then
    rm -rf $VENDOR
fi
mkdir $VENDOR
python3 -m pip install --download $VENDOR -r $REQUIREMENTS_PATH

# remove secrets
rm -rf $SECRETS_PATH

# prepare build manifest
echo "commit_sha=$(git rev-parse HEAD)" > build_info.ini

# assemble the artifact
VERSION=$(grep current_version .bumpversion.cfg | cut -d " " -f 3)
rm -rf $DELETED_ITEMS
zip -r platform-tests-${VERSION}.zip $VENDOR $ZIPPED_ITEMS
