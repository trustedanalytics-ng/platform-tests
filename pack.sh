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
SECRETS_PATH=project/secrets
REQUIREMENTS_PATH=./requirements.txt
ZIPPED_ITEMS="deploy/ project/ SMOKE_TESTS_README.md build_info.ini manifest.yml requirements.txt runtime.txt .bumpversion.cfg"
VIRTUALENV_PATH=~/virtualenvs/pyvenv_api_tests

# workaround for pip's issues with finding package dependencies
./deploy/create_virtualenv.sh $VIRTUALENV_PATH
source $VIRTUALENV_PATH/bin/activate

# prepare dependencies
if [ -d $VENDOR ]; then
    rm -rf $VENDOR
fi
mkdir $VENDOR
python3 -m pip install --download $VENDOR -r $REQUIREMENTS_PATH
# run script which downloads files for offline tests
python3 project/tests/fixtures/data_repo.py

deactivate

# prepare build manifest
echo "commit_sha=$(git rev-parse HEAD)" > build_info.ini

# assemble the artifact (excluding secrets)
VERSION=$(grep current_version .bumpversion.cfg | cut -d " " -f 3)
zip -r platform-tests-${VERSION}.zip $VENDOR $ZIPPED_ITEMS -x "$SECRETS_PATH/*"
