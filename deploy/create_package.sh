#!/bin/bash
#
# Copyright (c) 2015-2016 Intel Corporation
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
# Usage:
#   $ cd platform/tests/repo
#   $ bash deploy/create_package.sh
#   $ ls ..
#   TAP-tests-0.6.410.zip
set -e

APPLICATIONS_DIR="project/applications"
BUILD_SH="build.sh"
VENDOR="vendor"
REQUIREMENTS_PATH="requirements.txt"

ARCHIVED_ITEMS="deploy project vendor SMOKE_TESTS_README.md build_info.ini requirements.txt runtime.txt .bumpversion.cfg"

# silent version of pushd/popd
function pushd () {
    command pushd "$@" > /dev/null
}

function popd () {
    command popd "$@" > /dev/null
}

function build_applications() {
    echo "Building applications"
    pushd $APPLICATIONS_DIR
    find -type f -name $BUILD_SH | while read BUILD_SH_PATH; do
        APP_PATH=$(dirname $BUILD_SH_PATH)
        pushd $APP_PATH
        echo "Building $(pwd)"
        bash $BUILD_SH
        popd
    done
    popd
    echo "DONE!"
}

function download_platform_tests_pip_dependencies() {
    echo "Downloading platform-tests dependencies."
    if [ -e $VENDOR ]; then
        rm -rf $VENDOR
    fi
    mkdir $VENDOR

    pip download --dest $VENDOR -r $REQUIREMENTS_PATH
    pip download --dest $VENDOR pip setuptools
    echo "DONE!"
}

function create_build_info_file() {
    echo "Creating build_info.ini"
    echo "commit_sha=$(git rev-parse HEAD)" > build_info.ini
    echo "DONE!"
}

function create_package() {
    echo "Creating $ARCHIVE_PATH"
    zip -r $ARCHIVE_PATH $VENDOR $ARCHIVED_ITEMS \
        --exclude "project/secrets/*" "*/__pycache__/*" "*/.cache/*" "project/user_config.py"
    echo "DONE!"
}

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $PROJECT_DIR

VERSION=$(grep current_version .bumpversion.cfg | cut -d " " -f 3)
ARCHIVE_PATH=$(readlink -m ../TAP-tests-$VERSION.zip)

build_applications
download_platform_tests_pip_dependencies
create_build_info_file
create_package
