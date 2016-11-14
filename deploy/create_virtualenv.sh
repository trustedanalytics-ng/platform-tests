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

# Creates a python virtual environment with installed pip dependencies.
#
# Options:
#   --pyvenv <path>     Path to place where virtual environment should be created.
#                           Default is ~/virtualenvs/pyvenv_api_tests
#   --vendor <path>     Path to dir with python dependencies.
#                           By default dependencies are downloaded from the Internet.
#
# Usage:
#   $ cd platform/tests/repo
#   $ bash deploy/create_virtualenv.sh
#
# To create environment from offline package (create_package.sh):
#   $ cd platform/tests/repo
#   $ bash deploy/create_virtualenv.sh --vendor vendor
set -e

# make '--pyvenv' non-option argument
if [[ $1 && $1 != --* ]]; then
    eval set -- --pyvenv "$@"
fi

OPTS=`getopt -o p:v: --long pyvenv:,vendor: -n 'create_virtualenv' -- "$@"`

if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi

eval set -- "$OPTS"

PYVENV=~/virtualenvs/pyvenv_api_tests
VENDOR=

while true; do
    case "$1" in
        -e | --pyvenv ) PYVENV="$2"; shift; shift ;;
        -v | --vendor ) VENDOR="$2"; shift; shift ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done

REQUIREMENTS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )/requirements.txt"

# Create virtual env
python3 -m venv --without-pip $PYVENV
source $PYVENV/bin/activate

if [ -d "$VENDOR" ]; then
    echo "Offline installation from $VENDOR"

    # install pip from package
    PIP=$(find $VENDOR -name "pip-*")
    SETUPTOOLS=$(find $VENDOR -name "setuptools-*")
    python $PIP/pip install --no-index $SETUPTOOLS
    python $PIP/pip install --no-index $PIP

    # install platform-tests dependencies
    # workaround for git dependencies - locustio
    TEMPORARY_REQ=$(mktemp)
    grep -v "locustio" $REQUIREMENTS > $TEMPORARY_REQ
    python3 -m pip install --no-index --find-links=$VENDOR -r $TEMPORARY_REQ
    rm $TEMPORARY_REQ
    python3 -m pip install --no-index --find-links=$VENDOR $(find $VENDOR -name "locustio*zip")

else
    echo "Online installation"
    curl https://bootstrap.pypa.io/get-pip.py | python3
    python3 -m pip install -r $REQUIREMENTS
fi

deactivate
