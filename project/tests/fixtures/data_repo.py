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
import logging
import os
import sys
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)

DATA_REPO_PATH = os.path.join(os.path.dirname(__file__), '../../applications/data-repo')
FILES_DIRECTORY_NAME = 'files'
FILES_DIRECTORY_PATH = os.path.join(DATA_REPO_PATH, FILES_DIRECTORY_NAME)
DATA_REPO_TAR_PATH = os.path.join(DATA_REPO_PATH, "app.tar.gz")


def _get_filename_from_url(url):
    return url.rsplit('/', 1)[-1]


class DataFileKeys:
    TEST_TRANSFER = "test_transfer"
    KAFKA2GEARPUMP2HBASE = "kafka2gearpump2hbase"
    COMPLEXDAG_APP = "complexdag_app"
    HADOOP_MAPREDUCE_EXAMPLES = "hadoop_mapreduce_examples"


class Urls:

    DATA_FILES = {
        DataFileKeys.TEST_TRANSFER: "https://repo.gotapaas.eu/files/2_kilobytes.csv",
        DataFileKeys.KAFKA2GEARPUMP2HBASE: "https://repo.gotapaas.eu/files/gearpump-app-0.6.0-jar-with-dependencies.jar",
        DataFileKeys.COMPLEXDAG_APP: "https://repo.gotapaas.eu/files/complexdag-2.11.5-0.7.1-SNAPSHOT-assembly.jar",
        DataFileKeys.HADOOP_MAPREDUCE_EXAMPLES: "http://repo1.maven.org/maven2/org/apache/hadoop/hadoop-mapreduce-examples/2.2.0/hadoop-mapreduce-examples-2.2.0.jar",
    }

    class Url:
        def __init__(self, file_server_url, name):
            self.filename = _get_filename_from_url(Urls.DATA_FILES[name])
            self.url = "{}/{}/{}".format(file_server_url, FILES_DIRECTORY_NAME, self.filename)
            self.filepath = os.path.join(FILES_DIRECTORY_PATH, self.filename)

    def __init__(self, server_url):
        self.server_url = server_url

    @classmethod
    def download_data(cls):
        """Download files to data_repo/statics if not present already."""
        if not os.path.exists(FILES_DIRECTORY_PATH):
            os.mkdir(FILES_DIRECTORY_PATH)

        for name, url in cls.DATA_FILES.items():
            filename = _get_filename_from_url(url)
            filepath = os.path.join(FILES_DIRECTORY_PATH, filename)
            if not os.path.exists(filepath):
                logger.info("Downloading %s...", url)
                urlretrieve(url, filepath)

    def __getattr__(self, name):
        if name not in self.DATA_FILES:
            raise Exception("Unknown data file: {}".format(name))
        return self.Url(self.server_url, name)

    def __getitem__(self, key):
        return self.__getattr__(key)


def _initialize_logging():
    sh = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s: %(message)s", handlers=[sh],
                        level=logging.INFO)


if __name__ == '__main__':
    _initialize_logging()
    Urls.download_data()
