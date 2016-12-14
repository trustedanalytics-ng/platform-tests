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

import csv
from datetime import datetime
import io
import os
import xml.etree.ElementTree as ElementTree
import zipfile

import requests

TMP_FILE_DIR = "/tmp/test_files"
TMP_FILE_NAME = "test_file_{}.csv"
TEST_FILES = []  # list of generated files - used for cleanup


def generate_csv_file(column_count=10, size=None, row_count=10, file_name=None):
    """
    Return path to the new file.
    Pass row_count or size (in bytes) - if both are passed, size takes precedence.
    """
    os.makedirs(TMP_FILE_DIR, exist_ok=True)
    file_name = TMP_FILE_NAME.format(datetime.now().strftime('%Y%m%d_%H%M%S_%f')) if file_name is None else file_name
    file_path = os.path.join(TMP_FILE_DIR, file_name)
    with open(file_path, "w", newline="") as csv_file:
        if size == 0 or column_count == 0:
            return _add_generated_file(file_path)
        csv_writer = csv.writer(csv_file, lineterminator='\n')
        csv_writer.writerow(["COL_{}".format(i) for i in range(column_count)])
        row = ["0123456789" for _ in range(column_count)]
        if size is not None:
            while csv_file.tell() < size:
                csv_writer.writerow(row)
        else:
            for i in range(row_count):
                csv_writer.writerow(row)
    return _add_generated_file(file_path)


def _add_generated_file(file_path):
    """ Add file to list of generated files. """
    TEST_FILES.append(file_path)
    return file_path


def get_csv_record_count(file_path):
    """
    Return number of rows in chosen csv file
    """
    with open(file_path, newline="") as csv_file:
        csv_reader = csv.reader(csv_file)
        row_count = sum(1 for _ in csv_reader)
    return row_count


def get_csv_data(file_path):
    """
    Return data from chosen csv file
    """
    with open(file_path, newline="") as csv_file:
        return list(csv.reader(csv_file))


def get_csv_first_row(file_path):
    """
    Return first row from chosen csv file
    """
    with open(file_path, newline="") as csv_file:
        csv_reader = csv.reader(csv_file)
        data = csv_reader.__next__()
    return data


def download_file(url, save_file_name=None):
    """
    Download a file from provided url and return its directory
    """
    os.makedirs(TMP_FILE_DIR, exist_ok=True)
    if save_file_name is None:
        save_file_name = "test_file_{}.csv".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    file_path = os.path.join(TMP_FILE_DIR, save_file_name)
    r = requests.get(url)
    with open(file_path, "wb") as csv_file:
        csv_file.write(r.content)
    TEST_FILES.append(file_path)
    return file_path


def tear_down_test_files():
    while len(TEST_FILES) > 0:
        file_path = TEST_FILES.pop()
        os.remove(file_path)


def get_file_as_str_from_zip_archive(zip_file, file_path):
    if isinstance(zip_file, (str, bytes)):
        zip_file = io.BytesIO(zip_file)
    with zipfile.ZipFile(zip_file) as zf:
        return zf.read(file_path)


def get_value_from_core_site_xml(xml_content, name):
    root = ElementTree.fromstring(xml_content)
    property_tag = root.find("./property/[name='{}']".format(name))
    if property_tag is None:
        raise AssertionError("Missing tag 'name' with text '{}'.".format(name))
    value_tag = property_tag.find("./value")
    if value_tag is None:
        raise AssertionError("Missing tag 'value' in tag 'property' with text '{}'.".format(name))
    return value_tag.text


def get_link_content(link):
    """ Return content under the link as a string. """
    r = requests.get(link)
    r.raise_for_status()
    return r.content.decode()


def remove_if_exists(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


def save_text_file(data, file_name=None):
    file_name = TMP_FILE_NAME.format(datetime.now().strftime('%Y%m%d_%H%M%S_%f')) if file_name is None else file_name
    file_path = os.path.join(TMP_FILE_DIR, file_name)
    with open(file_path, "w") as text_file:
        text_file.write(data)
    _add_generated_file(file_path)
    return file_path
