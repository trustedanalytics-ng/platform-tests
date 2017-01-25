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
import os
import shutil
import subprocess

from modules.constants import ApplicationPath


SAMPLE_APPS_PATH = os.path.join(os.path.dirname(__file__), '../../applications/sample-apps')
TMP_FILE_DIR = "/tmp/test_files/sample_apps"
BUILD_SH = "build.sh"
TAR_GZ_EXT = ".tar.gz"
APP_BUILD_NAME = "app{}".format(TAR_GZ_EXT)


def _get_filename_from_url(url):
    return url.rsplit('/', 1)[-1]


class SampleAppKeys:
    TAPNG_PYTHON_APP = "tapng_python_app"
    TAPNG_GO_APP = "tapng_go_app"
    TAPNG_JAVA_APP = "tapng_java_app"
    TAPNG_NODEJS_APP = "tapng_nodejs_app"


class SampleApps:

    SAMPLE_APPS = {
        SampleAppKeys.TAPNG_PYTHON_APP: ApplicationPath.SAMPLE_PYTHON_APP,
        SampleAppKeys.TAPNG_GO_APP: ApplicationPath.SAMPLE_GO_APP,
        SampleAppKeys.TAPNG_JAVA_APP: ApplicationPath.SAMPLE_JAVA_APP,
        SampleAppKeys.TAPNG_NODEJS_APP: ApplicationPath.SAMPLE_NODEJS_APP
    }

    class SampleApp:
        def __init__(self, name):
            self.filename = "{}{}".format(name, TAR_GZ_EXT)
            self.filepath = os.path.join(TMP_FILE_DIR, self.filename)

    def __init__(self):
        self.prepare()

    def prepare(self):
        """ Build all sample apps and copy them to tmp directory"""
        if not os.path.exists(TMP_FILE_DIR):
            os.makedirs(TMP_FILE_DIR)

        for name, path in self.SAMPLE_APPS.items():
            tar_gz_path = self.build_app(path)
            self.move_app_to_data_repo(tar_gz_path, "{}{}".format(name, TAR_GZ_EXT))

    @classmethod
    def build_app(cls, directory):
        build_sh_path = os.path.join(directory, BUILD_SH)
        if os.path.exists(build_sh_path):
            subprocess.call("./" + BUILD_SH, cwd=directory)
        return os.path.join(directory, APP_BUILD_NAME)

    @classmethod
    def move_app_to_data_repo(cls, tar_gz_path, app_name):
        destination_path = os.path.join(TMP_FILE_DIR, app_name)
        subprocess.call(["mv", tar_gz_path, destination_path])
        return destination_path

    def __getattr__(self, name):
        if name not in self.SAMPLE_APPS:
            raise Exception("Unknown sample app: {}".format(name))
        return self.SampleApp(name)

    def __getitem__(self, key):
        return self.__getattr__(key)

    def cleanup(self):
        shutil.rmtree(TMP_FILE_DIR, ignore_errors=True)
