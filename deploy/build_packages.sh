#!/bin/bash
#
# Copyright (c) 2017 Intel Corporation
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

# A script that create a package to be used for running platform-tests offline.
# It will contain platform-tests and its pip dependencies, built applications and all test data.
#
echo "Runned"
set -e

APPLICATIONS_DIR="project/applications"

BUILD_SH="build.sh"
VENDOR="vendor"
REQUIREMENTS_PATH="requirements.txt"
TAR_NAME=app.tar.gz

ARCHIVED_ITEMS="deploy project vendor SMOKE_TESTS_README.md build_info.ini requirements.txt runtime.txt .bumpversion.cfg"

# silent version of pushd/popd
function pushd () {
    command pushd "$@" > /dev/null
}

function popd () {
    command popd > /dev/null
}

function build_applications() {
    echo "Building applications"
    pushd $APPLICATIONS_DIR
    find -type f -name $BUILD_SH | while read BUILD_SH_PATH; do
        APP_PATH=$(dirname $BUILD_SH_PATH)
        pushd $APP_PATH
        echo "Building $(pwd)"
        bash $BUILD_SH
        rm -f $TAR_NAME
        tar -zcvf $TAR_NAME *
        popd
    done
    popd
    echo "DONE!"
}


PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $PROJECT_DIR

VERSION=$(grep current_version .bumpversion.cfg | cut -d " " -f 3)
ARCHIVE_PATH=$(readlink -m ../TAP-tests-$VERSION.zip)

build_applications